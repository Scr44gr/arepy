from typing import Optional

from ...ecs.components import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3


class RigidBody2D(Component):
    def __init__(
        self,
        velocity: Vec2,
        acceleration: float = 24,
        deceleration: float = 14,
        max_velocity: int = 100,
    ) -> None:
        self.velocity = velocity
        self.acceleration = acceleration
        self.deceleration = deceleration
        self.max_velocity = max_velocity


class RigidBody3D(Component):
    """3D RigidBody component for physics simulation."""

    def __init__(
        self,
        velocity: Optional[Vec3] = None,
        acceleration: Optional[Vec3] = None,
        angular_velocity: Optional[Vec3] = None,
        max_velocity: float = 100.0,
    ) -> None:
        self.velocity = velocity if velocity is not None else Vec3(0.0, 0.0, 0.0)
        self.acceleration = acceleration if acceleration is not None else Vec3(0.0, 0.0, 0.0)
        self.angular_velocity = angular_velocity if angular_velocity is not None else Vec3(0.0, 0.0, 0.0)
        self.max_velocity = max_velocity
