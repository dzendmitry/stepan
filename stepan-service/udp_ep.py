import asyncio
import stepan

addr = '0.0.0.0'
port = 5006
status = "start"
buffer_size = 238592

class Endpoint(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.buffer = bytearray()

    def __put_buffer_to_queue(self):
        c = self.buffer.copy()
        stepan.q.put(c, block=False)
        self.buffer.clear()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if status != "stop":
            self.buffer.extend(data)
            if len(self.buffer) >= buffer_size:
                print('self buffer len: ', len(self.buffer))
                self.__put_buffer_to_queue()