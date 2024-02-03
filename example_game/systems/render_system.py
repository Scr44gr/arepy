from ctypes import pointer

from sdl2 import SDL_Rect, SDL_RenderCopy
from sdl2.ext import Renderer

from arepy.asset_store import AssetStore
from arepy.ecs.components import Component
from arepy.ecs.systems import System

from ..components import Sprite, Transform


class RenderSystem(System):
    def __init__(self) -> None:
        super().__init__()
        self.require_components([Transform, Sprite])

    def update(self, renderer: Renderer, asset_store: AssetStore):
        # RENDER BY Z-INDEX

        class RenderableEntity:
            def __init__(
                self, sprite_component: Sprite, transform_component: Transform
            ):
                self.sprite_component = sprite_component
                self.transform_component = transform_component

        renderable_entities = [
            RenderableEntity(
                entity.get_component(Sprite),
                entity.get_component(Transform),
            )
            for entity in self.get_entities()
        ]

        renderable_entities.sort(key=lambda entity: entity.sprite_component.z_index)

        for entity in renderable_entities:
            transform = entity.transform_component
            sprite = entity.sprite_component
            texture = asset_store.get_texture(sprite.asset_id)
            src_rect = sprite.src_rect
            dst_rect = SDL_Rect(
                w=int(sprite.width * transform.scale.x),
                h=int(sprite.height * transform.scale.y),
                x=int(transform.position.x),
                y=int(transform.position.y),
            )

            SDL_RenderCopy(
                renderer.sdlrenderer,
                texture,
                pointer(src_rect),
                pointer(dst_rect),
            )
