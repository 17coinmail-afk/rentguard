import os
import asyncio
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)

async def health(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get("/", health)
    
    try:
        from bot.config import BOT_TOKEN, WEBHOOK_URL
        logging.info(f"Config loaded. WEBHOOK_URL={WEBHOOK_URL}")
        
        from bot.database import init_db
        logging.info("Database module imported")
        
        await init_db()
        logging.info("Database initialized")
        
        from bot.handlers import start, landlord, payments, admin
        logging.info("Handlers imported")
        
        from aiogram import Bot, Dispatcher
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(start.router)
        dp.include_router(landlord.router)
        dp.include_router(payments.router)
        dp.include_router(admin.router)
        logging.info("Routers registered")
        
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        logging.info("Webhook handler registered")
        
        if WEBHOOK_URL:
            await bot.set_webhook(WEBHOOK_URL)
            logging.info(f"Webhook set to {WEBHOOK_URL}")
        
    except Exception as e:
        logging.error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info(f"Server started on port {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
