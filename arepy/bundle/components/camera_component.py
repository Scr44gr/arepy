from ...ecs import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3


class Camera2D(Component):
    def __init__(self, target: Vec2, position: Vec2, zoom: float = 1.0) -> None:
        self.target = target
        self.position = position
        self.zoom = zoom


class Camera3D(Component):
    def __init__(self, target: Vec3, position: Vec3, zoom: float = 1.0) -> None:
        self.target = target
        self.position = position
        self.zoom = zoom
