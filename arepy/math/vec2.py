import math


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def __eq__(self, other: "Vec2") -> bool:
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: "Vec2") -> bool:
        return self.x != other.x or self.y != other.y

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def __abs__(self) -> float:
        return math.hypot(self.x, self.y)

    def __round__(self, n: int = 0) -> "Vec2":
        return Vec2(round(self.x, n), round(self.y, n))

    def __floor__(self) -> "Vec2":
        return Vec2(math.floor(self.x), math.floor(self.y))

    def __ceil__(self) -> "Vec2":
        return Vec2(math.ceil(self.x), math.ceil(self.y))

    def __trunc__(self) -> "Vec2":
        return Vec2(math.trunc(self.x), math.trunc(self.y))

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        return f"Vec2({self.x}, {self.y})"

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> float:
        return (self.x, self.y)[index]

    def __setitem__(self, index: int, value: float):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        else:
            raise IndexError("Vec2 index out of range")

    def __iter__(self):
        yield self.x
        yield self.y

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length_squared(self) -> float:
        return self.x**2 + self.y**2

    def normalize(self) -> "Vec2":
        length = abs(self)
        if length == 0:
            return Vec2(0, 0)
        return Vec2(self.x / length, self.y / length)

    def normalize_ip(self) -> None:
        length = abs(self)
        if length == 0:
            self.x, self.y = 0, 0
        else:
            self.x /= length
            self.y /= length

    def lerp(self, other: "Vec2", t: float) -> "Vec2":
        return Vec2(self.x + (other.x - self.x) * t, self.y + (other.y - self.y) * t)

    def distance_to(self, other: "Vec2") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def angle_to(self, other: "Vec2") -> float:
        return math.atan2(other.y - self.y, other.x - self.x)

    def rotate(self, angle: float) -> "Vec2":
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vec2(self.x * cos_a - self.y * sin_a, self.x * sin_a + self.y * cos_a)

    def scale_ip(self, scalar: float) -> None:
        self.x *= scalar
        self.y *= scalar

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


def vec2(x: float, y: float) -> Vec2:
    return Vec2(x, y)


def vec2_zero() -> Vec2:
    return Vec2(0, 0)
