#!/usr/bin/env python

from socket import *
import sys
from scipy.io import wavfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('client')


def read_data(path):
    if len(path) == 0:
        raise FileNotFoundError
    fs, fdata = wavfile.read(path)
    logger.info('numpy shape: {}'.format(fdata.shape))
    return fdata.tobytes()


host = sys.argv[1]
port = 5006
buf = 1024
addr = (host,port)
file_name=sys.argv[2]

data = read_data(file_name)
logger.info('data length: {}'.format(len(data)))

s = socket(AF_INET, SOCK_DGRAM)
for i in range(0, len(data), buf):
    s.sendto(data[i:i+buf], addr)
s.close()