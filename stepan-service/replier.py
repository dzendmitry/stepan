import threading
import queue

q = queue.Queue()

def run():
    while True:
        play_sound = q.get()
        print(play_sound)

def start():
    t = threading.Thread(target=run)
    t.start()
