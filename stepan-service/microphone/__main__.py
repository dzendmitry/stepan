import pyaudio
import socket
import time

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512

host = '127.0.0.1'
port = 5006
addr = (host,port)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def callback(in_data, frame_count, time_info, status):
    s.sendto(in_data, addr)
    return (None, pyaudio.paContinue)

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, stream_callback=callback)
stream.start_stream()

while stream.is_active():
    time.sleep(10)