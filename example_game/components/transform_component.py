from glm import vec2

from arepy.ecs.components import Component


class Transform(Component):
    def __init__(self, position: vec2, rotation: float, scale: vec2) -> None:
        self.position = position
        self.rotation = rotation
        self.scale = scale
