from ...ecs import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3


class Camera2D(Component):
    def __init__(
        self, target: Vec2, offset: Vec2, zoom: float = 1.0, rotation: float = 0.0
    ) -> None:
        self.target = target
        self.offset = offset
        self.zoom = zoom
        self.rotation = rotation
        self._ref = None


class Camera3D(Component):
    def __init__(self, target: Vec3, offset: Vec3, zoom: float = 1.0) -> None:
        self.target = target
        self.offset = offset
        self.zoom = zoom
        self._ref = None
