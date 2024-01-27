import logging
from ctypes import c_long, pointer
from typing import Tuple

from glm import vec2
from sdl2 import SDL_QueryTexture, SDL_Rect, SDL_RenderCopy
from sdl2.ext import Renderer

from arepy import Arepy
from arepy.asset_store import AssetStore
from arepy.ecs.components import Component
from arepy.ecs.systems import System


class Transform(Component):
    def __init__(self, position: vec2, rotation: float, scale: vec2) -> None:
        self.position = position
        self.rotation = rotation
        self.scale = scale


class Velocity(Component):
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Health(Component):
    hp: int


class MovementSystem(System):
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self.require_component(Transform)
        self.require_component(Velocity)

    def update(self, delta_time: float):
        self.logger.info("Updating MovementSystem")
        for entity in self.get_system_entities():
            transform = entity.get_component(Transform)
            velocity = entity.get_component(Velocity)

            transform.position.x += velocity.x * delta_time
            transform.position.y += velocity.y * delta_time
            self.logger.info(
                f"Entity {entity} moved to Vec({transform.position.x:.2f}, {transform.position.y:.2f})"
            )


class Sprite(Component):
    def __init__(
        self,
        width: int,
        height: int,
        asset_id: str,
        src_rect: Tuple[int, int] = (0, 0),
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


class RenderSystem(System):
    def __init__(self) -> None:
        self.require_component(Transform)
        self.require_component(Sprite)

    def update(self, renderer: Renderer, asset_store: AssetStore):
        for entity in self.get_system_entities():
            transform = entity.get_component(Transform)
            sprite = entity.get_component(Sprite)
            texture = asset_store.get_texture(sprite.asset_id)
            src_rect = sprite.src_rect
            dst_rect = SDL_Rect(
                w=sprite.width,
                h=sprite.height,
                x=int(transform.position.x),
                y=int(transform.position.y),
            )

            SDL_RenderCopy(
                renderer.sdlrenderer,
                texture,
                pointer(src_rect),
                pointer(dst_rect),
            )


class MyGame(Arepy):
    title: str = "My Game"
    screen_width: int = 640
    screen_height: int = 480
    max_frame_rate: int = 60
    fullscreen: bool = False
    debug: bool = True

    def setup(self):
        # init engine
        self.init()
        # add assets
        self.get_asset_store().load_texture(
            self.renderer, "mahoraga", "./assets/makoraga.png"
        )

        # Player Creation
        entity_builder = self.create_entity()
        entity_builder.with_component(
            Transform(position=vec2(0, 0), rotation=0, scale=vec2(1, 1))
        )
        entity_builder.with_component(Velocity(x=30, y=30))
        entity_builder.with_component(Health(hp=100))
        entity_builder.with_component(Sprite(width=64, height=64, asset_id="mahoraga"))
        # A player is born
        player = entity_builder.build()

        # Enemy Creation

        # System Creation
        self.add_system(MovementSystem)
        self.add_system(RenderSystem)

    def level(self, level: int):
        print(f"Level: {level}")

    def on_startup(self):
        ...

    def on_shutdown(self):
        ...

    def on_update(self):
        self.get_system(MovementSystem).update(delta_time=self.delta_time)

    def on_render(self):
        self.get_system(RenderSystem).update(
            renderer=self.renderer,
            asset_store=self.get_asset_store(),
        )


if __name__ == "__main__":
    arepy = MyGame()
    arepy.setup()
    arepy.run()
