from typing import Optional

from ...ecs import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3


class Transform(Component):
    def __init__(
        self,
        position: Vec2 = Vec2(0, 0),
        scale: Vec2 = Vec2(1, 1),
        origin: Vec2 = Vec2(0, 0),
        rotation: float = 0,
    ):
        self.position = position
        self.scale = scale
        self.rotation = rotation
        self.origin = origin


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
