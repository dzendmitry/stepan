from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription

import json
import logging
import uuid

import udp_ep

addr = '0.0.0.0'
port = 8080

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('pc')
pcs = set()


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
    elif uri == '/offer':

        if request.method == "OPTIONS":
            return web.Response(headers={
                "Access-Control-Allow-Origin": request.headers["Origin"],
                "Access-Control-Allow-Headers": "content-type",
            })

        params = await request.json()
        offer = RTCSessionDescription(
            sdp=params['sdp'],
            type=params['type'])

        pc = RTCPeerConnection()
        pc_id = 'PeerConnection(%s)' % uuid.uuid4()
        pcs.add(pc)

        def log_info(msg, *args):
            logger.debug(pc_id + ' ' + msg, *args)

        log_info('Created for %s', request.remote)

        @pc.on('datachannel')
        def on_datachannel(channel):
            @channel.on('message')
            def on_message(message):
                if isinstance(message, str) and message.startswith('ping'):
                    channel.send('pong' + message[4:])

        @pc.on('iceconnectionstatechange')
        async def on_iceconnectionstatechange():
            log_info('ICE connection state is %s', pc.iceConnectionState)
            if pc.iceConnectionState == 'failed':
                await pc.close()
                pcs.discard(pc)

        @pc.on('track')
        def on_track(track):
            log_info('Track %s received', track.kind)

            if track.kind == 'audio':
                pass

            @track.on('ended')
            async def on_ended():
                log_info('Track %s ended', track.kind)

        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            headers={"Access-Control-Allow-Origin": "*"},
            content_type='application/json',
            text=json.dumps({
                'sdp': pc.localDescription.sdp,
                'type': pc.localDescription.type
            }))
    else:
        return web.Response(text="not implemented")


async def main():
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, addr, port)
    await site.start()
    print("======= Serving on http://127.0.0.1:8080/ ======")
