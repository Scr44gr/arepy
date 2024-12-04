from enum import Enum
from os.path import exists
from pathlib import Path
from typing import Any, Dict

from ..engine.renderer import ArepyTexture
from ..engine.renderer.renderer_2d import Renderer2D


class TextureFilter(Enum):
    NEAREST = 0
    LINEAR = 1


class AssetStore:
    textures: Dict[str, ArepyTexture] = dict()
    fonts: Dict[str, Any] = dict()

    def load_texture(
        self,
        renderer: Renderer2D,
        name: str,
        path: str,
    ) -> None:
        if not exists(path):
            raise FileNotFoundError(f"Texture file not found: {path}")

        self.textures[name] = renderer.create_texture(path=Path(path))

    def load_font(self, name: str, path: str, size: int) -> None: ...
    def get_texture(self, name: str) -> ArepyTexture:
        return self.textures[name]

    def get_font(self, name: str) -> Any:
        return self.fonts[name]

    def unload_texture(self, renderer: Renderer2D, name: str) -> None:

        texture = self.textures.pop(name)
        renderer.unload_texture(texture)
