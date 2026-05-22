from ...ecs import Component


class Transform(Component):
    position_x: float = 0.0
    position_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    origin_x: float = 0.0
    origin_y: float = 0.0
    rotation: float = 0.0


class Transform3D(Component):
    """3D Transform component that stores position, rotation, and scale in 3D space."""

    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0
