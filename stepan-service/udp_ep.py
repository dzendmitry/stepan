import asyncio
import queue
import numpy as np
import librosa

import noiser
import stepan

addr = '0.0.0.0'
port = 5006
status = "start"

class Endpoint(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.buffer = bytearray()
        self.for_stepan = bytearray()
        self.noise_buffer = bytearray()
        self.seq_of_silence_count = 0

    def __put_buffer_to_queue(self, q, buf):
        q.put(buf.copy(), block=False)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if status != "stop":
            if noiser.noise_level is None:
                self.noise_buffer.extend(data)
            else:
                if len(self.buffer) >= stepan.min_message_length:
                    mean_of_data = np.sum(librosa.feature.rmse(y=np.frombuffer(self.buffer, dtype=np.int16).astype(np.float32))[0])
                    if mean_of_data >= (noiser.noise_level + noiser.noise_upper_bound):
                        self.for_stepan.extend(self.buffer)
                        self.seq_of_silence_count = 0
                    else:
                        self.seq_of_silence_count += 1
                        self.noise_buffer.extend(self.buffer)
                    self.buffer.clear()
                else:
                    self.buffer.extend(data)
                if len(self.for_stepan) >= stepan.min_message_length and self.seq_of_silence_count >= stepan.silent_stepans:
                    self.seq_of_silence_count = 0
                    self.__put_buffer_to_queue(stepan.q, self.for_stepan)
                    self.for_stepan.clear()
            try:
                command = noiser.commands_queue.get(block=False)
                if isinstance(command, noiser.GetNoiseBuffer):
                    self.__put_buffer_to_queue(noiser.noise_queue, self.noise_buffer)
                    self.noise_buffer.clear()
            except queue.Empty:
                pass