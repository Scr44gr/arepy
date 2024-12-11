# create a new logger
import logging
from os import getenv
from sys import stdout

try:
    from dotenv import find_dotenv, load_dotenv

    # load environment variables from .env file
    load_dotenv(find_dotenv())
except ImportError:
    ...

logger_level = int(getenv("LOG_LEVEL", 50))

log_color = {
    0: "\033[0m",
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

from bitarray import bitarray


class Signature:
    __slots__ = ["__bits", "__flipped"]

    def __init__(self, size: int):
        self.__bits = bitarray(size)
        self.__bits.setall(False)
        self.__flipped = False

    def set(self, index, value: bool):
        self.__bits[index] = value

    def flip(self):
        self.__flipped = not self.__flipped
        self.__bits = ~self.__bits

    def clear_bit(self, index: int):
        self.__bits[index] = False

    def test(self, index: int):
        return self.__bits[index] == True

    def get_bits(self):
        return self.__bits

    def matches(self, other_signature: "Signature"):
        matches = (other_signature.get_bits() & self.get_bits()) == self.get_bits()
        return matches

    def clear(self):
        self.__bits.setall(False)

    @property
    def was_flipped(self):
        return self.__flipped
