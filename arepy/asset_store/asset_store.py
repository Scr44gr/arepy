from typing import Dict

from sdl2 import (
    SDL_CreateTextureFromSurface,
    SDL_DestroyTexture,
    SDL_FreeSurface,
    SDL_Texture,
)
from sdl2.ext import Renderer, load_image
from sdl2.sdlimage import IMG_Load
from sdl2.sdlttf import TTF_CloseFont, TTF_Font, TTF_OpenFont


class AssetStore:
    textures: Dict[str, SDL_Texture] = dict()
    fonts: Dict[str, TTF_Font] = dict()

    def load_texture(self, renderer: Renderer, name: str, path: str) -> None:
        surface = IMG_Load(path.encode("utf-8"))
        texture = SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface)
        SDL_FreeSurface(surface)

        self.textures[name] = texture

    def load_font(self, name: str, path: str, size: int) -> None:
        font = TTF_Font()
        font = TTF_OpenFont(path.encode("utf-8"), size)

        self.fonts[name] = font

    def get_texture(self, name: str) -> SDL_Texture:
        return self.textures[name]

    def get_font(self, name: str) -> TTF_Font:
        return self.fonts[name]

    def __del__(self):
        for texture in self.textures.values():
            SDL_DestroyTexture(texture)

        for font in self.fonts.values():
            TTF_CloseFont(font)
