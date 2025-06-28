from typing import Optional

from ...ecs import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3


class Camera2D(Component):
    """A 2D camera component that stores the camera's target, offset, zoom, rotation, and shake data."""

    def __init__(
        self,
        target: Vec2,
        offset: Vec2,
        zoom: float = 1.0,
        rotation: float = 0.0,
        shake_intensity: float = 0.0,
        shake_duration: float = 0.0,
        shake_timer: float = 0.0,
    ) -> None:
        self.target = target
        self.offset = offset
        self.zoom = zoom
        self.rotation = rotation
        self.shake_intensity = shake_intensity
        self.shake_duration = shake_duration
        self.shake_timer = shake_timer
        self.original_offset = offset.copy()
        self._ref = None


class Camera3D(Component):
    """A 3D camera component that stores position, target, up vector, and projection settings."""

    def __init__(
        self,
        position: Optional[Vec3] = None,
        target: Optional[Vec3] = None,
        up: Optional[Vec3] = None,
        fovy: float = 45.0,
        projection: int = 0,  # 0 = PERSPECTIVE, 1 = ORTHOGRAPHIC
    ) -> None:
        self.position = position if position is not None else Vec3(10.0, 10.0, 10.0)
        self.target = target if target is not None else Vec3(0.0, 0.0, 0.0)
        self.up = up if up is not None else Vec3(0.0, 1.0, 0.0)
        self.fovy = fovy  # Field of view Y in degrees
        self.projection = projection
        self._ref = None
