import os
import asyncio
import logging
import hmac
import hashlib
import urllib.parse
import json
from datetime import datetime, timedelta
from aiohttp import web
from sqlalchemy import select, func

logging.basicConfig(level=logging.INFO)

# ------------------ Telegram WebApp Auth ------------------

def validate_telegram_init_data(init_data: str) -> dict:
    if not init_data:
        raise ValueError("No init data")
    parsed = urllib.parse.parse_qs(init_data)
    params = {k: v[0] for k, v in parsed.items()}
    received_hash = params.pop("hash", "")
    if not received_hash:
        raise ValueError("No hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new("WebAppData".encode(), os.getenv("BOT_TOKEN", "").encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if computed_hash != received_hash:
        raise ValueError("Invalid hash")
    return json.loads(params.get("user", "{}"))

async def get_current_user(request) -> dict:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    try:
        return validate_telegram_init_data(init_data)
    except Exception as e:
        logging.warning(f"Auth failed: {e}")
        raise web.HTTPUnauthorized(text="Unauthorized")

async def get_session():
    from bot.database import async_session
    return async_session()

async def get_or_create_user(session, tg_user: dict):
    from bot.database import User
    from bot.config import TRIAL_DAYS
    tg_id = tg_user.get("id")
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            tg_id=tg_id,
            username=tg_user.get("username", ""),
            full_name=(tg_user.get("first_name", "") + " " + tg_user.get("last_name", "")).strip(),
            subscription_end=datetime.utcnow() + timedelta(days=TRIAL_DAYS)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

# ------------------ Handlers ------------------

async def health(request):
    return web.Response(text="RentGuard Mini App OK v2")

async def api_me(request):
    tg_user = await get_current_user(request)
    async with await get_session() as session:
        user = await get_or_create_user(session, tg_user)
        from bot.config import TRIAL_DAYS, PRICE_PER_PROPERTY
        return web.json_response({
            "id": user.id,
            "tg_id": user.tg_id,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "subscription_end": user.subscription_end.isoformat() if user.subscription_end else None,
            "trial_days": TRIAL_DAYS,
            "price_per_property": PRICE_PER_PROPERTY
        })

async def api_properties(request):
    tg_user = await get_current_user(request)
    async with await get_session() as session:
        user = await get_or_create_user(session, tg_user)
        from bot.database import Property
        result = await session.execute(select(Property).where(Property.owner_id == user.id))
        properties = result.scalars().all()
        return web.json_response([
            {"id": p.id, "name": p.name, "address": p.address, "rent_amount": p.rent_amount,
             "payment_day": p.payment_day, "tenant_name": p.tenant_name, "tenant_phone": p.tenant_phone,
             "tenant_tg": p.tenant_tg, "deposit": p.deposit} for p in properties
        ])

async def api_add_property(request):
    tg_user = await get_current_user(request)
    data = await request.json()
    async with await get_session() as session:
        user = await get_or_create_user(session, tg_user)
        from bot.database import Property
        prop = Property(
            owner_id=user.id,
            name=data.get("name", ""),
            address=data.get("address", ""),
            rent_amount=float(data.get("rent_amount", 0)),
            payment_day=int(data.get("payment_day", 1)),
            tenant_name=data.get("tenant_name", ""),
            tenant_phone=data.get("tenant_phone", ""),
            tenant_tg=data.get("tenant_tg", ""),
            deposit=float(data.get("deposit", 0)),
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)
        return web.json_response({"id": prop.id, "status": "ok"})

async def api_delete_property(request):
    tg_user = await get_current_user(request)
    prop_id = int(request.match_info["id"])
    async with await get_session() as session:
        user = await get_or_create_user(session, tg_user)
        from bot.database import Property
        result = await session.execute(select(Property).where(Property.id == prop_id, Property.owner_id == user.id))
        prop = result.scalar_one_or_none()
        if not prop:
            raise web.HTTPNotFound(text="Property not found")
        await session.delete(prop)
        await session.commit()
        return web.json_response({"status": "ok"})

async def api_stats(request):
    tg_user = await get_current_user(request)
    async with await get_session() as session:
        user = await get_or_create_user(session, tg_user)
        from bot.database import Property
        total_properties = (await session.execute(select(func.count(Property.id)).where(Property.owner_id == user.id))).scalar() or 0
        total_monthly_rent = (await session.execute(select(func.sum(Property.rent_amount)).where(Property.owner_id == user.id))).scalar() or 0
        return web.json_response({"total_properties": total_properties, "total_monthly_rent": total_monthly_rent})

# ------------------ Main ------------------

async def main():
    app = web.Application()

    static_path = os.path.join(os.path.dirname(__file__), "static")
    app.router.add_static("/static/", static_path)
    app.router.add_get("/", health)
    app.router.add_get("/app", lambda r: web.HTTPFound("/static/index.html"))

    app.router.add_get("/api/me", api_me)
    app.router.add_get("/api/properties", api_properties)
    app.router.add_post("/api/properties", api_add_property)
    app.router.add_delete("/api/properties/{id}", api_delete_property)
    app.router.add_get("/api/stats", api_stats)

    # Setup bot handlers BEFORE runner.setup()
    bot = None
    try:
        from bot.config import BOT_TOKEN, WEBHOOK_URL
        from bot.database import init_db
        from aiogram import Bot, Dispatcher
        from bot.handlers import start, landlord, payments, admin
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(start.router)
        dp.include_router(landlord.router)
        dp.include_router(payments.router)
        dp.include_router(admin.router)
        logging.info("Bot routers registered")

        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        logging.info("Webhook handler registered")
    except Exception as e:
        logging.error(f"Bot setup error: {e}")
        import traceback
        traceback.print_exc()

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info(f"Server started on port {port}")

    # Async init after server is up
    if bot:
        try:
            await init_db()
            logging.info("Database initialized")
            from bot.config import WEBHOOK_URL
            if WEBHOOK_URL:
                await bot.set_webhook(WEBHOOK_URL)
                logging.info(f"Webhook set to {WEBHOOK_URL}")
            logging.info("Bot fully initialized")
        except Exception as e:
            logging.error(f"Bot async init error: {e}")
            import traceback
            traceback.print_exc()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
