import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://rentguard-v47c.onrender.com")
WEBHOOK_PATH = "/webhook"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message()
async def echo(message: types.Message):
    if message.text == "/start":
        await message.answer(f"👋 Привет, {message.from_user.full_name}! Бот работает.")
    elif message.text == "/admin":
        if message.from_user.id == ADMIN_ID:
            await message.answer("✅ Админ-панель доступна.")
        else:
            await message.answer("❌ Нет доступа.")
    else:
        await message.answer(f"Ты написал: {message.text}")

async def on_startup():
    await bot.set_webhook(WEBHOOK_HOST + WEBHOOK_PATH)
    logging.info("Webhook set")

async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

async def health(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get("/", health)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info(f"Server started on port {port}")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
