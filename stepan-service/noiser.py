import threading
import time
import datetime
import queue
import numpy as np
import librosa

import stepan

noise_level = None
noise_upper_bound = 10000

commands_queue = queue.Queue()

noise_queue = queue.Queue()


class GetNoiseBuffer:
    pass


time_to_sleep = 10 # seconds


def run():
    global noise_level

    while True:
        commands_queue.put(GetNoiseBuffer())
        noise_bytes = noise_queue.get()
        noise_data = np.frombuffer(noise_bytes, dtype=np.int16).astype(np.float32)

        rmss = np.zeros(59, dtype=np.float32)
        count = 0
        for limit in range(0, len(noise_data), stepan.min_message_in_samples):
            rms = librosa.feature.rmse(y=noise_data[limit:limit+stepan.min_message_in_samples])[0]
            if len(rms) != len(rmss):
                continue
            rmss += rms
            count += 1

        if count > 1:
            noise_level = np.sum(rmss) / count
        print(datetime.datetime.now(), 'noise level: ', noise_level)

        time.sleep(time_to_sleep)


def start():
    t = threading.Thread(target=run)
    t.start()
