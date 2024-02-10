from abc import ABC, abstractmethod
from enum import Enum


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
    def render(self, *args, **kwargs):
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def create_texture(self, path: str) -> ArepyTexture:
        pass

    @abstractmethod
    def remove_texture(self, texture: ArepyTexture):
        pass

    @abstractmethod
    def draw_rect(
        self, x: int, y: int, width: int, height: int, color: tuple[int, int, int, int]
    ):
        pass

    def set_window_size(self, new_size: tuple[int, int]):
        assert new_size[0] > 0 and new_size[1] > 0
        self._window_size = new_size

    def get_window_size(self) -> tuple[int, int]:
        return self._window_size

    def get_screen_size(self) -> tuple[int, int]:
        return self._screen_size
