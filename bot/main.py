import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiohttp import web
from bot.config import BOT_TOKEN, WEBHOOK_URL
from bot.database import init_db
from bot.handlers import start, landlord, payments, admin
from bot.utils.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Register routers
dp.include_router(start.router)
dp.include_router(landlord.router)
dp.include_router(payments.router)
dp.include_router(admin.router)


async def on_startup():
    await init_db()
    setup_scheduler(bot)
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set to {WEBHOOK_URL}")
    logging.info("Bot started!")


async def on_shutdown():
    if WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()


async def healthcheck(request):
    return web.Response(text="OK", status=200)


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    app.router.add_get("/", healthcheck)
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info(f"Server started on port {port}")
    
    if WEBHOOK_URL:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        await asyncio.Event().wait()
    else:
        # Polling mode: run healthcheck server + polling
        polling_task = asyncio.create_task(dp.start_polling(bot))
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
