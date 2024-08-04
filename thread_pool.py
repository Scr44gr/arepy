import threading
from queue import Queue
from typing import Callable

# test the thread pool


def test_task():
    time.sleep(0.04)
    for _ in range(1000):
        pass


import time

if __name__ == "__main__":
    pool = ThreadPool(16)
    start_time = time.time()
    for _ in range(1000):
        pool.add_task(test_task)
    pool.start_workers()
