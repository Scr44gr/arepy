from dataclasses import dataclass
from typing import Optional


class ArepyTexture:
    def __init__(self, texture_id: int, size: tuple[int, int]):
        self.texture_id = texture_id
        self._texture_size = size
        self._ref: object = None

    def get_size(self) -> tuple[int, int]:
        return self._texture_size

    def unload(self) -> None: ...


@dataclass
class Rect:
    x: float
    y: float
    width: Optional[int]
    height: Optional[int]

    def to_tuple(self) -> tuple[float, float, Optional[int], Optional[int]]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class Color:
    r: int
    g: int
    b: int
    a: int

    def normalize(self) -> tuple[float, float, float, float]:
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)
