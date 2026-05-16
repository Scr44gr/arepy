from typing import Optional

from ...ecs import Component
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


class Transform(Component):
    position_x: float
    position_y: float
    scale_x: float
    scale_y: float
    origin_x: float
    origin_y: float
    rotation: float

    def __init__(
        self,
        position: Optional[Vec2] = None,
        scale: Optional[Vec2] = None,
        origin: Optional[Vec2] = None,
        rotation: float = 0,
    ):
        super().__init__()
        self.position = position if position is not None else Vec2(0, 0)
        self.scale = scale if scale is not None else Vec2(1, 1)
        self.rotation = rotation
        self.origin = origin if origin is not None else Vec2(0, 0)

    @property
    def position(self) -> Vec2:
        return get_vec2_view(self, "_position_view", "position_x", "position_y")

    @position.setter
    def position(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "position_x", "position_y")

    @property
    def scale(self) -> Vec2:
        return get_vec2_view(self, "_scale_view", "scale_x", "scale_y")

    @scale.setter
    def scale(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "scale_x", "scale_y")

    @property
    def origin(self) -> Vec2:
        return get_vec2_view(self, "_origin_view", "origin_x", "origin_y")

    @origin.setter
    def origin(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "origin_x", "origin_y")


class Transform3D(Component):
    """3D Transform component that stores position, rotation, and scale in 3D space."""

    position_x: float
    position_y: float
    position_z: float
    rotation_x: float
    rotation_y: float
    rotation_z: float
    scale_x: float
    scale_y: float
    scale_z: float

    def __init__(
        self,
        position: Optional[Vec3] = None,
        rotation: Optional[Vec3] = None,
        scale: Optional[Vec3] = None,
    ) -> None:
        super().__init__()
        self.position = position if position is not None else Vec3(0.0, 0.0, 0.0)
        self.rotation = (
            rotation if rotation is not None else Vec3(0.0, 0.0, 0.0)
        )  # Euler angles in degrees
        self.scale = scale if scale is not None else Vec3(1.0, 1.0, 1.0)

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
    def rotation(self) -> Vec3:
        return get_vec3_view(
            self,
            "_rotation_view",
            "rotation_x",
            "rotation_y",
            "rotation_z",
        )

    @rotation.setter
    def rotation(self, value: Vec3Like) -> None:
        assign_vec3_fields(
            self,
            value,
            "rotation_x",
            "rotation_y",
            "rotation_z",
        )

    @property
    def scale(self) -> Vec3:
        return get_vec3_view(
            self,
            "_scale_view",
            "scale_x",
            "scale_y",
            "scale_z",
        )

    @scale.setter
    def scale(self, value: Vec3Like) -> None:
        assign_vec3_fields(self, value, "scale_x", "scale_y", "scale_z")
