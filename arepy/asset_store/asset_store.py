from enum import Enum
from os.path import exists
from pathlib import Path
from typing import Dict

from freetype import Face

from ..engine.renderer import ArepyTexture
from ..engine.renderer.renderer_2d_repository import Renderer2DRepository


class TextureFilter(Enum):
    NEAREST = 0
    LINEAR = 1


class AssetStore:
    textures: Dict[str, ArepyTexture] = dict()
    fonts: Dict[str, Face] = dict()

    def load_texture(
        self,
        renderer: Renderer2DRepository,
        name: str,
        path: str,
    ) -> None:
        if not exists(path):
            raise FileNotFoundError(f"Texture file not found: {path}")

        self.textures[name] = renderer.create_texture(path=Path(path))

    def load_font(self, name: str, path: str, size: int) -> None:
        font = Face(path)
        font.set_pixel_sizes(0, size)
        self.fonts[name] = font

    def get_texture(self, name: str) -> ArepyTexture:
        return self.textures[name]

    def get_font(self, name: str) -> Face:
        return self.fonts[name]
