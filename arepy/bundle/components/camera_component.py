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
    def __init__(self, target: Vec3, offset: Vec3, zoom: float = 1.0) -> None:
        self.target = target
        self.offset = offset
        self.zoom = zoom
        self._ref = None
