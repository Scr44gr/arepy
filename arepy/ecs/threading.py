import time
from queue import Queue
from threading import Event, Lock

ECS_LOCK = Lock()
ECS_KILL_THREAD_EVENT = Event()
ECS_EXECUTOR_QUEUE = Queue()
FIXED_FRAME_TIME = 1 / 60


def run_ecs_thread_executor():
    while not ECS_KILL_THREAD_EVENT.is_set():
        with ECS_LOCK:
            while not ECS_EXECUTOR_QUEUE.empty():
                system, args = ECS_EXECUTOR_QUEUE.get_nowait()
                system(*args)
                ECS_EXECUTOR_QUEUE.task_done()
        time.sleep(FIXED_FRAME_TIME)
