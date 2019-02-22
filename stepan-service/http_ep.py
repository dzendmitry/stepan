from aiohttp import web
import udp_ep

addr = '0.0.0.0'
port = 8080


async def handler(request):
    uri = str(request.rel_url)
    print("Request: ", uri)
    if uri == '/start':
        udp_ep.status = "start"
        return web.Response(text=udp_ep.status)
    elif uri == '/stop':
        udp_ep.status = "stop"
        return web.Response(text=udp_ep.status)
    elif uri == '/status':
        return web.Response(text=udp_ep.status)
    else:
        return web.Response(text="not implemented")


async def main():
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, addr, port)
    await site.start()
    print("======= Serving on http://127.0.0.1:8080/ ======")
