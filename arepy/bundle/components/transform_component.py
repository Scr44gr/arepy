from glm import vec2

from ...ecs import Component


class Transform(Component):
    def __init__(
        self, position: vec2 = vec2(0, 0), scale: vec2 = vec2(1, 1), rotation: float = 0
    ):
        self.position = position
        self.scale = scale
        self.rotation = rotation
