from ...ecs import Component


class Camera2D(Component):
    """A 2D camera component that stores the camera's target, offset, zoom, rotation, and shake data."""

    target_x: float = 0.0
    target_y: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    zoom: float = 1.0
    rotation: float = 0.0
    shake_intensity: float = 0.0
    shake_duration: float = 0.0
    shake_timer: float = 0.0
    original_offset_x: float = 0.0
    original_offset_y: float = 0.0


class Camera3D(Component):
    """A 3D camera component that stores position, target, up vector, and projection settings."""

    position_x: float = 10.0
    position_y: float = 10.0
    position_z: float = 10.0
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    up_x: float = 0.0
    up_y: float = 1.0
    up_z: float = 0.0
    fovy: float = 45.0
    projection: int = 0
