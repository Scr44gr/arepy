from enum import IntEnum
from typing import Optional

from ...ecs import Component
from ...math.vec3 import Vec3


class Light3DType(IntEnum):
    """Enum-like class for light types."""

    DIRECTIONAL = 0
    POINT = 1
    SPOT = 2


class Light3D(Component):
    """Component representing a 3D light source."""

    def __init__(
        self,
        light_type: Light3DType = Light3DType.DIRECTIONAL,
        enabled: bool = True,
        position: Optional[Vec3] = None,
        target: Optional[Vec3] = None,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        intensity: float = 1.0,
        attenuation: float = 0.0,
    ):
        self.light_type = light_type
        self.enabled = enabled
        self.position = position if position is not None else Vec3(0.0, 0.0, 0.0)
        self.target = target if target is not None else Vec3(0.0, 0.0, 0.0)
        self.color = color
        self.intensity = intensity
        self.attenuation = attenuation
        self._light_id: Optional[int] = None  # For shader management
