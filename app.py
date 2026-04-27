from aiohttp import web
import os

async def hello(request):
    return web.Response(text="Hello, world")

app = web.Application()
app.router.add_get("/", hello)

port = int(os.getenv("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)
