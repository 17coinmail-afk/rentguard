import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

API_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message()
async def echo(message: types.Message):
    if message.text == "/start":
        await message.answer(f"Привет, {message.from_user.full_name}! Aiogram + webhook работает.")
    elif message.text == "/admin":
        if message.from_user.id == ADMIN_ID:
            await message.answer("✅ Админ-панель")
        else:
            await message.answer("❌ Нет доступа")
    else:
        await message.answer(f"Ты написал: {message.text}")

async def health(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get("/", health)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info(f"Server started on port {port}")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
