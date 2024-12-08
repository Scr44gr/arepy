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

    def __mul__(self, other: float) -> "Vec2":
        return Vec2(self.x * other, self.y * other)

    def __truediv__(self, other: float) -> "Vec2":
        return Vec2(self.x / other, self.y / other)

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return f"Vec2({self.x}, {self.y})"

    def __eq__(self, other: "Vec2"):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: "Vec2"):
        return self.x != other.x or self.y != other.y

    def __len__(self):
        return 2  # Vec2 is a 2D vector :p

    def __getitem__(self, index: int):
        items = [self.x, self.y]
        return items[index]

    def __setitem__(self, key: int, value: float):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Vec2 only has 2 components")

    def __iter__(self):
        yield self.x
        yield self.y

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __pos__(self):
        return Vec2(self.x, self.y)

    def __abs__(self):
        return (self.x**2 + self.y**2) ** 0.5

    def __round__(self, n: int = 0):
        return Vec2(round(self.x, n), round(self.y, n))

    def __floor__(self):
        return Vec2(math.floor(self.x), math.floor(self.y))

    def __ceil__(self):
        return Vec2(math.ceil(self.x), math.ceil(self.y))

    def __trunc__(self):
        return Vec2(math.trunc(self.x), math.trunc(self.y))

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y


def vec2(x: float, y: float) -> Vec2:
    assert isinstance(x, (int, float)), "x must be a number"
    assert isinstance(y, (int, float)), "y must be a number"
    return Vec2(x, y)


def vec2_zero() -> Vec2:
    return Vec2(0, 0)
