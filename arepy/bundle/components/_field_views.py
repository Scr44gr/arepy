from __future__ import annotations

from numbers import Integral
from typing import Any, Iterable

from ...math.vec2 import Vec2
from ...math.vec3 import Vec3

Vec2Like = Vec2 | tuple[float, float] | list[float]
Vec3Like = Vec3 | tuple[float, float, float] | list[float]


class Vec2FieldView(Vec2):
    __slots__ = ("_owner", "_x_field", "_y_field")

    def __init__(self, owner: object, x_field: str, y_field: str) -> None:
        self._owner = owner
        self._x_field = x_field
        self._y_field = y_field

    @property
    def x(self) -> Any:
        return getattr(self._owner, self._x_field)

    @x.setter
    def x(self, value: Any) -> None:
        setattr(self._owner, self._x_field, value)

    @property
    def y(self) -> Any:
        return getattr(self._owner, self._y_field)

    @y.setter
    def y(self, value: Any) -> None:
        setattr(self._owner, self._y_field, value)


class Vec3FieldView(Vec3):
    __slots__ = ("_owner", "_x_field", "_y_field", "_z_field")

    def __init__(self, owner: object, x_field: str, y_field: str, z_field: str) -> None:
        self._owner = owner
        self._x_field = x_field
        self._y_field = y_field
        self._z_field = z_field

    @property
    def x(self) -> Any:
        return getattr(self._owner, self._x_field)

    @x.setter
    def x(self, value: Any) -> None:
        setattr(self._owner, self._x_field, value)

    @property
    def y(self) -> Any:
        return getattr(self._owner, self._y_field)

    @y.setter
    def y(self, value: Any) -> None:
        setattr(self._owner, self._y_field, value)

    @property
    def z(self) -> Any:
        return getattr(self._owner, self._z_field)

    @z.setter
    def z(self, value: Any) -> None:
        setattr(self._owner, self._z_field, value)


def assign_vec2_fields(owner: object, value: Vec2Like, x_field: str, y_field: str) -> None:
    x_value, y_value = _pair(value)
    setattr(owner, x_field, x_value)
    setattr(owner, y_field, y_value)


def assign_vec3_fields(
    owner: object,
    value: Vec3Like,
    x_field: str,
    y_field: str,
    z_field: str,
) -> None:
    x_value, y_value, z_value = _triple(value)
    setattr(owner, x_field, x_value)
    setattr(owner, y_field, y_value)
    setattr(owner, z_field, z_value)


def get_vec2_view(owner: object, cache_attr: str, x_field: str, y_field: str) -> Vec2FieldView:
    view = getattr(owner, cache_attr, None)
    if view is None:
        view = Vec2FieldView(owner, x_field, y_field)
        setattr(owner, cache_attr, view)
    return view


def get_vec3_view(
    owner: object,
    cache_attr: str,
    x_field: str,
    y_field: str,
    z_field: str,
) -> Vec3FieldView:
    view = getattr(owner, cache_attr, None)
    if view is None:
        view = Vec3FieldView(owner, x_field, y_field, z_field)
        setattr(owner, cache_attr, view)
    return view


def assign_fields(owner: object, values: Iterable[Any], *field_names: str) -> None:
    items = tuple(values)
    if len(items) != len(field_names):
        raise ValueError(
            f"Expected {len(field_names)} values, received {len(items)}"
        )
    for field_name, value in zip(field_names, items):
        setattr(owner, field_name, value)


def field_tuple(owner: object, *field_names: str) -> tuple[Any, ...]:
    return tuple(getattr(owner, field_name) for field_name in field_names)


class InternedStringTable:
    __slots__ = ("_value_to_handle", "_handle_to_value")

    def __init__(self) -> None:
        self._value_to_handle: dict[str, int] = {}
        self._handle_to_value: dict[int, str] = {}

    def intern(self, value: str | None) -> int:
        if value is None:
            return 0
        handle = self._value_to_handle.get(value)
        if handle is not None:
            return handle

        handle = len(self._value_to_handle) + 1
        self._value_to_handle[value] = handle
        self._handle_to_value[handle] = value
        return handle

    def resolve(self, handle: object) -> object:
        if handle is None:
            return None
        if not isinstance(handle, Integral):
            return handle
        handle_value = int(handle)
        if handle_value == 0:
            return None
        try:
            return self._handle_to_value[handle_value]
        except KeyError as error:
            raise ValueError(f"Unknown interned string handle: {handle_value}") from error


def _pair(value: Vec2Like) -> tuple[float, float]:
    first, second = _unpack_exactly(value, 2)
    return float(first), float(second)


def _triple(value: Vec3Like) -> tuple[float, float, float]:
    first, second, third = _unpack_exactly(value, 3)
    return float(first), float(second), float(third)


def _unpack_exactly(value: Iterable[float], size: int) -> tuple[float, ...]:
    items = tuple(value)
    if len(items) != size:
        raise ValueError(f"Expected {size} values, received {len(items)}")
    return items