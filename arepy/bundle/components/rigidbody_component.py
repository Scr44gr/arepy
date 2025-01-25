from ...ecs.components import Component
from ...math.vec2 import Vec2


class RigidBody2D(Component):
    def __init__(
        self,
        velocity: Vec2 = Vec2(0, 0),
        acceleration: float = 24,
        deceleration: float = 14,
        max_velocity: int = 100,
    ) -> None:
        self.velocity = velocity
        self.acceleration = acceleration
        self.deceleration = deceleration
        self.max_velocity = max_velocity
