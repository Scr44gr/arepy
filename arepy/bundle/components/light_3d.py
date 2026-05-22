from enum import IntEnum

from ...ecs import Component


class Light3DType(IntEnum):
    """Enum-like class for light types."""

    DIRECTIONAL = 0
    POINT = 1
    SPOT = 2


class Light3D(Component):
    """Component representing a 3D light source."""

    light_type_value: int = int(Light3DType.DIRECTIONAL)
    enabled: bool = True
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    color_r: float = 1.0
    color_g: float = 1.0
    color_b: float = 1.0
    color_a: float = 1.0
    intensity: float = 1.0
    attenuation: float = 0.0
