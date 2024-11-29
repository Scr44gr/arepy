from os import PathLike
from typing import Optional, Protocol

from ...bundle.components.camera_component import Camera2D
from . import ArepyTexture, Color, Rect


class Renderer2DRepository(Protocol):
    # Texture methods
    def create_texture(self, path: PathLike[str]) -> ArepyTexture: ...

    # Draw methods
    def draw_texture(
        self, texture: ArepyTexture, source: Rect, dest: Rect, color: Color
    ) -> None: ...
    def draw_texture_ex(
        self,
        texture: ArepyTexture,
        source: Rect,
        dest: Rect,
        rotation: float,
        color: Color,
    ) -> None: ...
    def draw_rectangle(self, rect: Rect, color: Color) -> None: ...
    def draw_points(self, points: list[tuple[float, float]], color: Color) -> None: ...
    def draw_lines(self, points: list[tuple[float, float]], color: Color) -> None: ...
    def draw_circle(
        self, center: tuple[float, float], radius: float, color: Color
    ) -> None: ...
    def draw_text(
        self, text: str, position: tuple[float, float], font_size: int, color: Color
    ) -> None: ...
    def draw_fps(
        self,
        position: tuple[int, int],
    ) -> None: ...

    # Frame methods
    def set_max_framerate(self, max_frame_rate: int) -> None: ...
    def clear(self, color: Color) -> None: ...
    def start_frame(self) -> None: ...
    def end_frame(self) -> None: ...
    def flush(self) -> None: ...
    def swap_buffers(self) -> None: ...
    def get_delta_time(self) -> float: ...
    def get_framerate(self) -> int: ...

    # Camera methods
    def add_camera(self, camera: Camera2D) -> None: ...
    def get_camera(self, id: int) -> Optional[Camera2D]: ...
    def remove_camera(self, id: int) -> None: ...
    def set_current_camera(self, id: int) -> None: ...
    @property
    def cameras(self) -> list[Camera2D]: ...
    @property
    def current_camera(self) -> Camera2D: ...
