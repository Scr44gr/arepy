from ...ecs.components import Component


class RigidBody2D(Component):
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    acceleration: float = 24.0
    deceleration: float = 14.0
    max_velocity: int = 100


class RigidBody3D(Component):
    """3D RigidBody component for physics simulation."""

    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    acceleration_x: float = 0.0
    acceleration_y: float = 0.0
    acceleration_z: float = 0.0
    angular_velocity_x: float = 0.0
    angular_velocity_y: float = 0.0
    angular_velocity_z: float = 0.0
    max_velocity: float = 100.0
