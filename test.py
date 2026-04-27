import os
from aiohttp import web

async def health(request):
    return web.Response(text="OK")

app = web.Application()
app.router.add_get("/", health)

port = int(os.getenv("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)
