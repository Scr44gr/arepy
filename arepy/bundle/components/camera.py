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


class Camera2D(Component):
    """A 2D camera component that stores the camera's target, offset, zoom, rotation, and shake data."""

    target_x: float
    target_y: float
    offset_x: float
    offset_y: float
    zoom: float
    rotation: float
    shake_intensity: float
    shake_duration: float
    shake_timer: float
    original_offset_x: float
    original_offset_y: float

    def __init__(
        self,
        target: Vec2,
        offset: Vec2,
        zoom: float = 1.0,
        rotation: float = 0.0,
        shake_intensity: float = 0.0,
        shake_duration: float = 0.0,
        shake_timer: float = 0.0,
    ) -> None:
        super().__init__()
        self.target = target
        self.offset = offset
        self.zoom = zoom
        self.rotation = rotation
        self.shake_intensity = shake_intensity
        self.shake_duration = shake_duration
        self.shake_timer = shake_timer
        self.original_offset = offset.copy()
        self._ref = None

    @property
    def target(self) -> Vec2:
        return get_vec2_view(self, "_target_view", "target_x", "target_y")

    @target.setter
    def target(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "target_x", "target_y")

    @property
    def offset(self) -> Vec2:
        return get_vec2_view(self, "_offset_view", "offset_x", "offset_y")

    @offset.setter
    def offset(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "offset_x", "offset_y")

    @property
    def original_offset(self) -> Vec2:
        return get_vec2_view(
            self,
            "_original_offset_view",
            "original_offset_x",
            "original_offset_y",
        )

    @original_offset.setter
    def original_offset(self, value: Vec2Like) -> None:
        assign_vec2_fields(self, value, "original_offset_x", "original_offset_y")


class Camera3D(Component):
    """A 3D camera component that stores position, target, up vector, and projection settings."""

    position_x: float
    position_y: float
    position_z: float
    target_x: float
    target_y: float
    target_z: float
    up_x: float
    up_y: float
    up_z: float
    fovy: float
    projection: int

    def __init__(
        self,
        position: Optional[Vec3] = None,
        target: Optional[Vec3] = None,
        up: Optional[Vec3] = None,
        fovy: float = 45.0,
        projection: int = 0,  # 0 = PERSPECTIVE, 1 = ORTHOGRAPHIC
    ) -> None:
        super().__init__()
        self.position = position if position is not None else Vec3(10.0, 10.0, 10.0)
        self.target = target if target is not None else Vec3(0.0, 0.0, 0.0)
        self.up = up if up is not None else Vec3(0.0, 1.0, 0.0)
        self.fovy = fovy  # Field of view Y in degrees
        self.projection = projection
        self._ref = None

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
    def up(self) -> Vec3:
        return get_vec3_view(self, "_up_view", "up_x", "up_y", "up_z")

    @up.setter
    def up(self, value: Vec3Like) -> None:
        assign_vec3_fields(self, value, "up_x", "up_y", "up_z")
