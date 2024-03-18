from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class RendererType(Enum):
    OPENGL = "OpenGL"


class ArepyTexture:
    def __init__(self, texture_id: int, size: tuple[int, int]):
        self.texture_id = texture_id
        self._texture_size = size

    def get_size(self) -> tuple[int, int]:
        return self._texture_size


class BaseRenderer(ABC):

    def __init__(
        self,
        screen_size: tuple[int, int],
        window_size: tuple[int, int],
        *args,
        **kwargs
    ):
        self._screen_size = screen_size
        self._window_size = window_size

    @abstractmethod
    def start_frame(self, *args, **kwargs):
        """Start a frame"""
        pass

    @abstractmethod
    def end_frame(self, *args, **kwargs):
        """
        End the frame and swap the buffers
        """
        pass

    @abstractmethod
    def draw_sprite(
        self,
        texture: ArepyTexture,
        src_rect: Optional[tuple[float, float, float, float]],
        src_dest: Optional[tuple[float, float, float, float]],
        color: tuple[int, int, int, int],
    ):
        pass

    @abstractmethod
    def flush(self, *args, **kwargs):
        """
        Flush the renderer
        """
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def draw_rect(
        self, x: int, y: int, width: int, height: int, color: tuple[int, int, int, int]
    ):
        pass

    @abstractmethod
    def draw_circle(
        self, x: int, y: int, radius: int, color: tuple[int, int, int, int]
    ):
        pass

    @abstractmethod
    def draw_line(
        self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int, int]
    ):
        pass

    @abstractmethod
    def create_texture(self, path: str) -> ArepyTexture:
        pass

    @abstractmethod
    def remove_texture(self, texture: ArepyTexture):
        pass

    def set_window_size(self, new_size: tuple[int, int]):
        assert new_size[0] > 0 and new_size[1] > 0
        self._window_size = new_size

    def get_window_size(self) -> tuple[int, int]:
        return self._window_size

    def get_screen_size(self) -> tuple[int, int]:
        return self._screen_size
