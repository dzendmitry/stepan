import asyncio
import threading
import queue
from enum import Enum

q = queue.Queue()

channel = None


class Commands(Enum):
    STATE_SKIPPED = -1
    NOISE = 0
    STEPAN = 1
    SHOW_CATALOG_API = 2
    SHOW_K8S_API = 3
    SHOW_ITEM_API = 4


def run():
    loop = asyncio.new_event_loop()
    while True:
        command = q.get()
        if command == Commands.STATE_SKIPPED:
            print("RESPONSE: State skipped")
            if channel is not None:
                send_command(Commands.STATE_SKIPPED, loop)
        elif command == Commands.NOISE:
            print("RESPONSE: Noise")
        elif command == Commands.STEPAN:
            print("RESPONSE: Yes, My Lord!")
            if channel is not None:
                send_command(Commands.STEPAN, loop)
        elif command == Commands.SHOW_CATALOG_API:
            print("RESPONSE: Showing CATALOG API dashboard")
            if channel is not None:
                send_command(Commands.SHOW_CATALOG_API, loop)
        elif command == Commands.SHOW_K8S_API:
            print("RESPONSE: Showing K8S dashboard")
            if channel is not None:
                send_command(Commands.SHOW_K8S_API, loop)
        elif command == Commands.SHOW_ITEM_API:
            print("RESPONSE: Showing ITEM API dashboard")
            if channel is not None:
                send_command(Commands.SHOW_ITEM_API, loop)
        else:
            print("RESPONSE: Unknown command")


def send_command(cmd, loop):
    loop.run_until_complete(send_command_async(str(cmd)))


async def send_command_async(cmd):
    channel.send(cmd)


def start():
    t = threading.Thread(target=run)
    t.start()
