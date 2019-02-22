#!/usr/bin/env python

import asyncio
import stepan
import replier
import refresher
import noiser

import udp_ep
import http_ep

if __name__ == "__main__":
    # stepan
    stepan.init_models()
    stepan.start()
    # refresher
    refresher.start()
    # replier
    replier.start()
    # noise lvl updater
    noiser.start()

    loop = asyncio.get_event_loop()
    # Prepare udp server
    t = loop.create_datagram_endpoint(udp_ep.Endpoint, local_addr=(udp_ep.addr, udp_ep.port))
    loop.run_until_complete(t)
    # Prepare http server
    loop.run_until_complete(http_ep.main())
    loop.run_forever()
