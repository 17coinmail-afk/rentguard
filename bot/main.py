import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
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


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    if WEBHOOK_URL:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        from aiohttp import web
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=8080)
        await site.start()
        logging.info("Webhook server started on port 8080")
        
        # Keep running
        await asyncio.Event().wait()
    else:
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())