from enum import IntEnum
from numbers import Integral
from typing import Optional

from ...ecs import Component
from ...math.vec3 import Vec3
from ._field_views import (
    Vec3Like,
    assign_fields,
    assign_vec3_fields,
    field_tuple,
    get_vec3_view,
)


class Light3DType(IntEnum):
    """Enum-like class for light types."""

    DIRECTIONAL = 0
    POINT = 1
    SPOT = 2


class Light3D(Component):
    """Component representing a 3D light source."""

    light_type_value: int
    enabled: bool
    position_x: float
    position_y: float
    position_z: float
    target_x: float
    target_y: float
    target_z: float
    color_r: float
    color_g: float
    color_b: float
    color_a: float
    intensity: float
    attenuation: float

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
        super().__init__()
        self.light_type = light_type
        self.enabled = enabled
        self.position = position if position is not None else Vec3(0.0, 0.0, 0.0)
        self.target = target if target is not None else Vec3(0.0, 0.0, 0.0)
        self.color = color
        self.intensity = intensity
        self.attenuation = attenuation
        self._light_id: Optional[int] = None  # For shader management

    @property
    def light_type(self) -> object:
        value = self.light_type_value
        if isinstance(value, Integral):
            return Light3DType(int(value))
        return value

    @light_type.setter
    def light_type(self, value: Light3DType | int) -> None:
        self.light_type_value = int(value)

    @property
    def position(self) -> Vec3:
        return get_vec3_view(
            self,
            "_position_view",
            "position_x",
            "position_y",
            "position_z",
        )

    @position.setter
    def position(self, value: Vec3Like) -> None:
        assign_vec3_fields(
            self,
            value,
            "position_x",
            "position_y",
            "position_z",
        )

    @property
    def target(self) -> Vec3:
        return get_vec3_view(
            self,
            "_target_view",
            "target_x",
            "target_y",
            "target_z",
        )

    @target.setter
    def target(self, value: Vec3Like) -> None:
        assign_vec3_fields(
            self,
            value,
            "target_x",
            "target_y",
            "target_z",
        )

    @property
    def color(self) -> tuple[object, object, object, object]:
        return field_tuple(self, "color_r", "color_g", "color_b", "color_a")

    @color.setter
    def color(self, value: tuple[float, float, float, float]) -> None:
        assign_fields(self, value, "color_r", "color_g", "color_b", "color_a")
