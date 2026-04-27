from aiohttp import web
import os

# Test if aiogram import works
from aiogram import Bot
API_TOKEN = os.getenv("BOT_TOKEN", "")
bot = Bot(token=API_TOKEN)

async def hello(request):
    return web.Response(text="Hello, world with aiogram")

app = web.Application()
app.router.add_get("/", hello)

port = int(os.getenv("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)
