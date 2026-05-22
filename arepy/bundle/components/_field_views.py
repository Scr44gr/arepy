from __future__ import annotations

from numbers import Integral


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