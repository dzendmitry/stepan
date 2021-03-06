import threading
import time
import stepan
import queue
import datetime
import logging

import replier
from replier import Commands

logger = logging.getLogger('refresher')

q = queue.Queue()

time_to_wait_command_in_seconds = 30
time_skew_seconds = 2


def run():
    while True:
        ts = q.get()
        deadline = ts + datetime.timedelta(0, time_to_wait_command_in_seconds)
        diff = deadline - datetime.datetime.now()
        if diff.total_seconds() <= time_skew_seconds:
            continue
        time.sleep(time_to_wait_command_in_seconds)
        logger.info("refresher: switching state...")
        if stepan.state != stepan.States.WAIT_STEPAN:
            stepan.state = stepan.States.WAIT_STEPAN
            replier.q.put(Commands.STATE_SKIPPED)
        logger.info("refresher: state switched")


def start():
    t = threading.Thread(target=run)
    t.start()
