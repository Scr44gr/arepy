from typing import Optional

from ...ecs.components import Component
from ...math.vec2 import Vec2
from ...math.vec3 import Vec3
from ._field_views import (
    Vec2Like,
    Vec3Like,
    assign_vec2_fields,
    assign_vec3_fields,
    get_vec2_view,
    get_vec3_view,
)


class RigidBody2D(Component):
    velocity_x: float
    velocity_y: float
    acceleration: float
    deceleration: float
    max_velocity: int

    def __init__(
        self,
        velocity: Vec2,
        acceleration: float = 24,
        deceleration: float = 14,
        max_velocity: int = 100,
    ) -> None:
        super().__init__()
        self.velocity = velocity
        self.acceleration = acceleration
        self.deceleration = deceleration
        self.max_velocity = max_velocity

    @property
    def velocity(self) -> Vec2:
        return get_vec2_view(self, "_velocity_view", "velocity_x", "velocity_y")

    @velocity.setter
    def velocity(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "velocity_x", "velocity_y")


class RigidBody3D(Component):
    """3D RigidBody component for physics simulation."""

    velocity_x: float
    velocity_y: float
    velocity_z: float
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float
    max_velocity: float

    def __init__(
        self,
        velocity: Optional[Vec3] = None,
        acceleration: Optional[Vec3] = None,
        angular_velocity: Optional[Vec3] = None,
        max_velocity: float = 100.0,
    ) -> None:
        super().__init__()
        self.velocity = velocity if velocity is not None else Vec3(0.0, 0.0, 0.0)
        self.acceleration = (
            acceleration if acceleration is not None else Vec3(0.0, 0.0, 0.0)
        )
        self.angular_velocity = (
            angular_velocity if angular_velocity is not None else Vec3(0.0, 0.0, 0.0)
        )
        self.max_velocity = max_velocity

    @property
    def velocity(self) -> Vec3:
        return get_vec3_view(
            self,
            "_velocity_view",
            "velocity_x",
            "velocity_y",
            "velocity_z",
        )

    @velocity.setter
    def velocity(self, value: Vec3Like) -> None:
        assign_vec3_fields(
            self,
            value,
            "velocity_x",
            "velocity_y",
            "velocity_z",
        )

    @property
    def acceleration(self) -> Vec3:
        return get_vec3_view(
            self,
            "_acceleration_view",
            "acceleration_x",
            "acceleration_y",
            "acceleration_z",
        )

    @acceleration.setter
    def acceleration(self, value: Vec3Like) -> None:
        assign_vec3_fields(
            self,
            value,
            "acceleration_x",
            "acceleration_y",
            "acceleration_z",
        )

    @property
    def angular_velocity(self) -> Vec3:
        return get_vec3_view(
            self,
            "_angular_velocity_view",
            "angular_velocity_x",
            "angular_velocity_y",
            "angular_velocity_z",
        )

    @angular_velocity.setter
    def angular_velocity(self, value: Vec3Like) -> None:
        assign_vec3_fields(
            self,
            value,
            "angular_velocity_x",
            "angular_velocity_y",
            "angular_velocity_z",
        )
