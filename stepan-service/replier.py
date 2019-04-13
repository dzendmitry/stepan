import asyncio
import threading
import queue
from enum import Enum

q = queue.Queue()

channel = None


class Commands(Enum):
    NOISE = 0
    STEPAN = 1
    SHOW_CATALOG_API = 2
    SHOW_K8S_API = 3
    SHOW_ITEM_API = 4


def run():
    loop = asyncio.new_event_loop()
    while True:
        command = q.get()
        if command == Commands.NOISE:
            print("RESPONSE: Noise")
        elif command == Commands.STEPAN:
            print("RESPONSE: Yes, My Lord!")
        elif command == Commands.SHOW_CATALOG_API:
            print("RESPONSE: Showing CATALOG API dashboard")
            if channel is not None:
                loop.run_until_complete(send_command(str(Commands.SHOW_CATALOG_API)))
        elif command == Commands.SHOW_K8S_API:
            print("RESPONSE: Showing K8S dashboard")
            if channel is not None:
                loop.run_until_complete(send_command(str(Commands.SHOW_K8S_API)))
        elif command == Commands.SHOW_ITEM_API:
            print("RESPONSE: Showing ITEM API dashboard")
            if channel is not None:
                loop.run_until_complete(send_command(str(Commands.SHOW_ITEM_API)))
        else:
            print("RESPONSE: Unknown command")


async def send_command(cmd):
    channel.send(cmd)


def start():
    t = threading.Thread(target=run)
    t.start()
