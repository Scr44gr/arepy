import math


class Vec3:

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other: float) -> "Vec3":
        return Vec3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other: float) -> "Vec3":
        return Vec3(self.x / other, self.y / other, self.z / other)

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"

    def __eq__(self, other: "Vec3"):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other: "Vec3"):
        return self.x != other.x or self.y != other.y or self.z != other.z

    def __len__(self):
        return 3  # Vec3 is a 3D vector :p

    def __getitem__(self, index: int):
        items = [self.x, self.y, self.z]
        return items[index]

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
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def normalize(self) -> "Vec3":
        return self / abs(self)

    def angle(self, other: "Vec3") -> float:
        return math.acos(self.dot(other) / (abs(self) * abs(other)))

    def project(self, other: "Vec3") -> "Vec3":
        return other * (self.dot(other) / other.dot(other))


def vec3(x: float, y: float, z: float) -> Vec3:
    assert isinstance(x, (int, float)), "x must be an int or a float"
    assert isinstance(y, (int, float)), "y must be an int or a float"
    assert isinstance(z, (int, float)), "z must be an int or a float"
    return Vec3(x, y, z)


def vec3_zero() -> Vec3:
    return Vec3(0, 0, 0)
