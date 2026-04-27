import os
import asyncio
from aiohttp import web

async def health(request):
    return web.Response(text="RentGuard Mini App OK v2")

async def main():
    app = web.Application()
    static_path = os.path.join(os.path.dirname(__file__), "static")
    app.router.add_static("/static/", static_path)
    app.router.add_get("/", health)
    app.router.add_get("/app", lambda r: web.HTTPFound("/static/index.html"))
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
