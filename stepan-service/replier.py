import threading
import queue
import subprocess
from enum import Enum

q = queue.Queue()


class Commands(Enum):
    NOISE = 0
    STEPAN = 1
    SHOW_CATALOG_API = 2
    SHOW_K8S_API = 3


def run():
    while True:
        command = q.get()
        if command == Commands.NOISE:
            print("RESPONSE: Noise")
        elif command == Commands.STEPAN:
            print("RESPONSE: Yes, My Lord!")
        elif command == Commands.SHOW_CATALOG_API:
            print("RESPONSE: Showing CATALOG API dashboard")
        elif command == Commands.SHOW_K8S_API:
            print("RESPONSE: Showing K8S dashboard")
        else:
            print("RESPONSE: Unknown command")


def start():
    t = threading.Thread(target=run)
    t.start()
