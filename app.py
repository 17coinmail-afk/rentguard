import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()

@router.message()
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

dp.include_router(router)

async def health(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get("/", health)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info(f"Server started on port {port}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
