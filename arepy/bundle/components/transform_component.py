from ...ecs import Component
from ...math.vec2 import Vec2


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
