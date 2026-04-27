import os
import json
import aiohttp
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = "https://rentguard-v47c.onrender.com/webhook"

async def health(request):
    return web.Response(text="OK")

async def webhook_handler(request):
    data = await request.json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        user = data["message"]["from"]
        
        if text == "/start":
            reply = f"👋 Привет, {user.get('first_name', '')}! Бот работает."
        elif text == "/admin":
            if user.get("id") == ADMIN_ID:
                reply = "✅ Админ-панель доступна."
            else:
                reply = "❌ Нет доступа."
        else:
            reply = f"Ты написал: {text}"
        
        await send_message(chat_id, reply)
    return web.Response(text="OK")

async def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

async def set_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"url": WEBHOOK_URL}) as resp:
            result = await resp.text()
            print("Webhook set:", result)

app = web.Application()
app.router.add_get("/", health)
app.router.add_post("/webhook", webhook_handler)

# Set webhook on startup
async def on_startup(app):
    await set_webhook()

app.on_startup.append(on_startup)

port = int(os.getenv("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)
