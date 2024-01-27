from typing import Dict

from sdl2 import (
    SDL_CreateTextureFromSurface,
    SDL_DestroyTexture,
    SDL_FreeSurface,
    SDL_Texture,
)
from sdl2.ext import Renderer, load_image
from sdl2.sdlimage import IMG_Load, IMG_LoadTexture


class AssetStore:
    textures: Dict[str, SDL_Texture] = dict()

    def load_texture(self, renderer: Renderer, name: str, path: str) -> None:
        surface = IMG_Load(path.encode("utf-8"))
        texture = SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface)
        SDL_FreeSurface(surface)

        self.textures[name] = texture

    def get_texture(self, name: str) -> SDL_Texture:
        return self.textures[name]

    def __del__(self):
        for texture in self.textures.values():
            SDL_DestroyTexture(texture)
