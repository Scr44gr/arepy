# create a new logger
import logging
from os import getenv
from sys import stdout

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
logger_level = int(getenv("LOG_LEVEL", "INFO"))

log_color = {
    10: "\033[33m",
    20: "\033[32m",
    30: "\033[33m",
    40: "\033[31m",
    50: "\033[35m",
}
logging.basicConfig(
    # [2024-01-25T17:57:04Z INFO  arepita::systems::camera_movement_system] camera x: 798
    format=f"[%(asctime)s [{log_color[logger_level]}%(levelname)s{log_color[logger_level].split('[')[0]}[0m] %(name)s::%(funcName)s] %(message)s",
    level=logger_level,
    handlers=[
        logging.StreamHandler(stdout),
        logging.StreamHandler(
            open(
                getenv("LOG_FILE", "arepy.log"),
                "a" if getenv("LOG_APPEND", "0") == "1" else "w",
            )
        ),
    ],
)


class Signature:
    def __init__(self, size: int):
        self.__bits = size * 0

    def set(self, index, value: bool):
        assert value in (0, 1)
        self.__bits |= value << index

    def clear_bit(self, index: int):
        assert index >= 0
        self.__bits &= ~(1 << index)

    def test(self, index: int):
        assert index >= 0
        return (self.__bits & (1 << index)) != 0

    def matches(self, signature: "Signature"):
        return self.__bits & signature.__bits == self.__bits
