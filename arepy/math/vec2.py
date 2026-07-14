import math

from numpy.typing import NDArray


class Vec2:
    __slots__ = (
        "_x",
        "_y",
        "_storage",
        "_index",
    )
    _storage_epoch = 0

    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y
        self._storage: tuple[NDArray[object], NDArray[object]] | None = None
        self._index: int | None = None

    @classmethod
    def from_storage(
        cls,
        x_storage: NDArray[object],
        y_storage: NDArray[object],
        index: int,
    ) -> "Vec2":
        vector = cls.__new__(cls)
        vector._x = 0.0
        vector._y = 0.0
        vector._storage = None
        vector._index = None
        vector._bind_storage(x_storage, y_storage, index)
        return vector

    def _bind_storage(
        self,
        x_storage: NDArray[object],
        y_storage: NDArray[object],
        index: int,
    ) -> None:
        """Bind this vector to array storage without replacing its identity."""

        storage = self._storage
        if (
            self._index == index
            and storage is not None
            and storage[0] is x_storage
            and storage[1] is y_storage
        ):
            return
        self._storage = (x_storage, y_storage)
        self._index = index
        Vec2._storage_epoch += 1

    @classmethod
    def _get_storage_epoch(cls) -> int:
        return Vec2._storage_epoch

    @property
    def x(self) -> float:
        if self._storage is None or self._index is None:
            return self._x
        return float(self._storage[0][self._index])

    @x.setter
    def x(self, value: float) -> None:
        if self._storage is None or self._index is None:
            self._x = value
            return
        self._storage[0][self._index] = value

    @property
    def y(self) -> float:
        if self._storage is None or self._index is None:
            return self._y
        return float(self._storage[1][self._index])

    @y.setter
    def y(self, value: float) -> None:
        if self._storage is None or self._index is None:
            self._y = value
            return
        self._storage[1][self._index] = value

    def __add__(self, other: "Vec2") -> "Vec2":
        if not isinstance(other, Vec2):
            return NotImplemented
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        if not isinstance(other, Vec2):
            return NotImplemented
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        if not isinstance(scalar, int | float):
            return NotImplemented
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vec2":
        return self * scalar

    def __truediv__(self, scalar: float) -> "Vec2":
        if not isinstance(scalar, int | float):
            return NotImplemented
        return Vec2(self.x / scalar, self.y / scalar)

    def __iadd__(self, other: "Vec2") -> "Vec2":
        if not isinstance(other, Vec2):
            return NotImplemented
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other: "Vec2") -> "Vec2":
        if not isinstance(other, Vec2):
            return NotImplemented
        self.x -= other.x
        self.y -= other.y
        return self

    def __imul__(self, scalar: float) -> "Vec2":
        if not isinstance(scalar, int | float):
            return NotImplemented
        self.x *= scalar
        self.y *= scalar
        return self

    def __itruediv__(self, scalar: float) -> "Vec2":
        if not isinstance(scalar, int | float):
            return NotImplemented
        self.x /= scalar
        self.y /= scalar
        return self

    def __eq__(self, other: "Vec2") -> bool:
        if not isinstance(other, Vec2):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: "Vec2") -> bool:
        if not isinstance(other, Vec2):
            return NotImplemented
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
        if not isinstance(other, Vec2):
            return NotImplemented
        return self.x * other.x + self.y * other.y

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalize(self) -> "Vec2":
        length = abs(self)
        if math.isclose(length, 0.0):
            return Vec2(0, 0)
        return Vec2(self.x / length, self.y / length)

    def normalize_ip(self) -> None:
        length = abs(self)
        if math.isclose(length, 0.0):
            self.x, self.y = 0, 0
        else:
            self.x /= length
            self.y /= length

    def lerp(self, other: "Vec2", t: float) -> "Vec2":
        if not isinstance(other, Vec2):
            return NotImplemented
        return Vec2(self.x + (other.x - self.x) * t, self.y + (other.y - self.y) * t)

    def distance_to(self, other: "Vec2") -> float:
        if not isinstance(other, Vec2):
            return NotImplemented
        return math.hypot(self.x - other.x, self.y - other.y)

    def angle_to(self, other: "Vec2") -> float:
        if not isinstance(other, Vec2):
            return NotImplemented
        return math.atan2(other.y - self.y, other.x - self.x)

    def rotate(self, angle: float) -> "Vec2":
        x = self.x
        y = self.y
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vec2(x * cos_a - y * sin_a, x * sin_a + y * cos_a)

    def scale_ip(self, scalar: float) -> None:
        self *= scalar

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


def vec2(x: float, y: float) -> Vec2:
    return Vec2(x, y)


def vec2_zero() -> Vec2:
    return Vec2(0, 0)
