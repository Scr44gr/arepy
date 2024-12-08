from ...ecs.components import Component
from ...math.vec2 import Vec2


class RigidBody2D(Component):
    def __init__(
        self, velocity: Vec2 = Vec2(0, 0), acceleration: Vec2 = Vec2(0, 0)
    ) -> None:
        self.velocity = velocity
        self.acceleration = acceleration
