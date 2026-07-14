import math

from numpy.typing import NDArray


class Vec3:

    __slots__ = (
        "_x",
        "_y",
        "_z",
        "_storage",
        "_index",
    )
    _storage_epoch = 0

    def __init__(self, x: float, y: float, z: float):
        self._x = x
        self._y = y
        self._z = z
        self._storage: tuple[NDArray[object], NDArray[object], NDArray[object]] | None = None
        self._index: int | None = None

    @classmethod
    def from_storage(
        cls,
        x_storage: NDArray[object],
        y_storage: NDArray[object],
        z_storage: NDArray[object],
        index: int,
    ) -> "Vec3":
        vector = cls.__new__(cls)
        vector._x = 0.0
        vector._y = 0.0
        vector._z = 0.0
        vector._storage = None
        vector._index = None
        vector._bind_storage(x_storage, y_storage, z_storage, index)
        return vector

    def _bind_storage(
        self,
        x_storage: NDArray[object],
        y_storage: NDArray[object],
        z_storage: NDArray[object],
        index: int,
    ) -> None:
        """Bind this vector to array storage without replacing its identity."""

        storage = self._storage
        if (
            self._index == index
            and storage is not None
            and storage[0] is x_storage
            and storage[1] is y_storage
            and storage[2] is z_storage
        ):
            return
        self._storage = (x_storage, y_storage, z_storage)
        self._index = index
        Vec3._storage_epoch += 1

    @classmethod
    def _get_storage_epoch(cls) -> int:
        return Vec3._storage_epoch

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

    @property
    def z(self) -> float:
        if self._storage is None or self._index is None:
            return self._z
        return float(self._storage[2][self._index])

    @z.setter
    def z(self, value: float) -> None:
        if self._storage is None or self._index is None:
            self._z = value
            return
        self._storage[2][self._index] = value

    def __add__(self, other: "Vec3") -> "Vec3":
        if not isinstance(other, Vec3):
            return NotImplemented
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        if not isinstance(other, Vec3):
            return NotImplemented
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other: float) -> "Vec3":
        if not isinstance(other, int | float):
            return NotImplemented
        return Vec3(self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other: float) -> "Vec3":
        return self * other

    def __truediv__(self, other: float) -> "Vec3":
        if not isinstance(other, int | float):
            return NotImplemented
        return Vec3(self.x / other, self.y / other, self.z / other)

    def __iadd__(self, other: "Vec3") -> "Vec3":
        if not isinstance(other, Vec3):
            return NotImplemented
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __isub__(self, other: "Vec3") -> "Vec3":
        if not isinstance(other, Vec3):
            return NotImplemented
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __imul__(self, other: float) -> "Vec3":
        if not isinstance(other, int | float):
            return NotImplemented
        self.x *= other
        self.y *= other
        self.z *= other
        return self

    def __itruediv__(self, other: float) -> "Vec3":
        if not isinstance(other, int | float):
            return NotImplemented
        self.x /= other
        self.y /= other
        self.z /= other
        return self

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"

    def __eq__(self, other: "Vec3"):
        if not isinstance(other, Vec3):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other: "Vec3"):
        if not isinstance(other, Vec3):
            return NotImplemented
        return self.x != other.x or self.y != other.y or self.z != other.z

    def __len__(self):
        return 3  # Vec3 is a 3D vector :p

    def __getitem__(self, index: int):
        return (self.x, self.y, self.z)[index]

    def __setitem__(self, key: int, value: float):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value
        else:
            raise IndexError("Vec3 only has 3 components")

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __pos__(self):
        return Vec3(self.x, self.y, self.z)

    def __abs__(self):
        return math.hypot(self.x, self.y, self.z)

    def cross(self, other: "Vec3") -> "Vec3":
        if not isinstance(other, Vec3):
            return NotImplemented
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def dot(self, other: "Vec3") -> float:
        if not isinstance(other, Vec3):
            return NotImplemented
        return self.x * other.x + self.y * other.y + self.z * other.z

    def normalize(self) -> "Vec3":
        length = abs(self)
        if math.isclose(length, 0.0):
            return Vec3(0, 0, 0)
        return self / length

    def normalize_ip(self) -> None:
        length = abs(self)
        if math.isclose(length, 0.0):
            self.x = 0
            self.y = 0
            self.z = 0
            return

        self.x /= length
        self.y /= length
        self.z /= length

    def angle(self, other: "Vec3") -> float:
        if not isinstance(other, Vec3):
            return NotImplemented

        self_length = abs(self)
        other_length = abs(other)
        denominator = self_length * other_length
        if math.isclose(denominator, 0.0):
            return 0.0

        cosine = self.dot(other) / denominator
        clamped_cosine = max(-1.0, min(1.0, cosine))
        return math.acos(clamped_cosine)

    def project(self, other: "Vec3") -> "Vec3":
        if not isinstance(other, Vec3):
            return NotImplemented

        denominator = other.dot(other)
        if math.isclose(denominator, 0.0):
            return Vec3(0, 0, 0)

        return other * (self.dot(other) / denominator)

    def length(self) -> float:
        """Returns the length of the vector."""
        return abs(self)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y + self.z * self.z

    def scale_ip(self, scalar: float) -> None:
        self *= scalar

    def copy(self) -> "Vec3":
        return Vec3(self.x, self.y, self.z)

    def to_tuple(self) -> tuple[float, float, float]:
        """Returns the vector as a tuple."""
        return (self.x, self.y, self.z)


def vec3(x: float, y: float, z: float) -> Vec3:
    assert isinstance(x, (int, float)), "x must be an int or a float"
    assert isinstance(y, (int, float)), "y must be an int or a float"
    assert isinstance(z, (int, float)), "z must be an int or a float"
    return Vec3(x, y, z)


def vec3_zero() -> Vec3:
    return Vec3(0, 0, 0)
