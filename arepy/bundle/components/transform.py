from typing import Optional

from numpy.typing import NDArray

from ...ecs import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3


class Transform(Component):
    def __init__(
        self,
        position: Optional[Vec2] = None,
        scale: Optional[Vec2] = None,
        origin: Optional[Vec2] = None,
        rotation: float = 0,
    ):
        self.position = position if position is not None else Vec2(0, 0)
        self.scale = scale if scale is not None else Vec2(1, 1)
        self._rotation = rotation
        self._rotation_storage: NDArray[object] | None = None
        self._rotation_index = -1
        self.origin = origin if origin is not None else Vec2(0, 0)

    @property
    def rotation(self) -> float:
        storage = self._rotation_storage
        if storage is None:
            return self._rotation
        return float(storage[self._rotation_index])

    @rotation.setter
    def rotation(self, value: float) -> None:
        storage = self._rotation_storage
        if storage is None:
            self._rotation = value
            return
        storage[self._rotation_index] = value

    def _bind_scalar_storage(
        self, attribute_name: str, storage: NDArray[object], index: int
    ) -> None:
        if attribute_name != "rotation":
            raise AttributeError(
                f"Transform does not support scalar storage for '{attribute_name}'."
            )
        self._rotation_storage = storage
        self._rotation_index = index

    def _uses_scalar_storage(
        self, attribute_name: str, storage: NDArray[object], index: int
    ) -> bool:
        return (
            attribute_name == "rotation"
            and self._rotation_storage is storage
            and self._rotation_index == index
        )


class Transform3D(Component):
    """3D Transform component that stores position, rotation, and scale in 3D space."""

    def __init__(
        self,
        position: Optional[Vec3] = None,
        rotation: Optional[Vec3] = None,
        scale: Optional[Vec3] = None,
    ) -> None:
        self.position = position if position is not None else Vec3(0.0, 0.0, 0.0)
        self.rotation = (
            rotation if rotation is not None else Vec3(0.0, 0.0, 0.0)
        )  # Euler angles in degrees
        self.scale = scale if scale is not None else Vec3(1.0, 1.0, 1.0)
