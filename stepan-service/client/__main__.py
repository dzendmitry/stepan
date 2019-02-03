#!/usr/bin/env python

from socket import *
import sys
from scipy.io import wavfile

def read_data(path):
    if len(path) == 0:
        raise FileNotFoundError
    fs, fdata = wavfile.read(path)
    print('numpy shape: ', fdata.shape)
    return fdata.tobytes()

host = sys.argv[1]
port = 5006
buf = 1024
addr = (host,port)
file_name=sys.argv[2]

data = read_data(file_name)
print('data length: ', len(data))

s = socket(AF_INET, SOCK_DGRAM)
for i in range(0, len(data), buf):
    s.sendto(data[i:i+buf], addr)
s.close()