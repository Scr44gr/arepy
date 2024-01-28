from glm import vec2

from arepy.ecs.components import Component


class Rigidbody(Component):
    def __init__(self, velocity: vec2, acceleration: vec2) -> None:
        self.velocity = velocity
        self.acceleration = acceleration
