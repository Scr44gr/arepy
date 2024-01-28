from typing import Tuple

from sdl2 import SDL_Rect

from arepy.ecs.components import Component


class Sprite(Component):
    def __init__(
        self,
        width: int,
        height: int,
        asset_id: str,
        src_rect: Tuple[int, int] = (0, 0),
        z_index: int = 0,
    ) -> None:
        self.width = width
        self.height = height
        self.asset_id = asset_id
        self.src_rect = SDL_Rect(
            w=width,
            h=height,
            x=src_rect[0],
            y=src_rect[1],
        )
        self.z_index = z_index
