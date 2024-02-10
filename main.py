import OpenGL.GL as gl
import sdl2

from arepy import Arepy
from arepy.asset_store import AssetStore
from arepy.ecs import Component, System
from arepy.engine.renderer import BaseRenderer


class Position(Component):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Sprite(Component):
    def __init__(
        self,
        width: int,
        height: int,
        asset_id: str,
        src_rect=(0, 0),
        z_index: int = 0,
    ):
        self.width = width
        self.height = height
        self.asset_id = asset_id
        self.src_rect = src_rect
        self.z_index = z_index


class MovementSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Position, Velocity])

    def update(self, dt: float):
        for entity in self.get_entities():
            position = entity.get_component(Position)
            velocity = entity.get_component(Velocity)
            position.x += velocity.x * dt
            position.y += velocity.y * dt


class RenderSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Position, Sprite])

    def update(self, dt: float, renderer: BaseRenderer, asset_store: AssetStore):
        tick = sdl2.SDL_GetTicks()
        for entity in self.get_entities():
            position = entity.get_component(Position)
            sprite = entity.get_component(Sprite)
            texture_id = asset_store.get_texture(sprite.asset_id)
            # testing animation
            src_rect = (
                32 if tick // 50 % 4 == 0 else 0,
                sprite.src_rect[1],
                sprite.width,
                sprite.height,
            )
            dest_rect = (position.x, position.y, sprite.width, sprite.height)
            renderer.render(texture_id, src_rect, dest_rect)
            renderer.draw_rect(
                position.x - sprite.width // 2,
                position.y - sprite.height // 2,
                sprite.width,
                sprite.height,
                (255, 0, 0, 255),
            )


if __name__ == "__main__":
    game = Arepy()
    game.init()
    game.title = "My awesome game"
    game.debug = True
    # load assets
    asset_store = game.get_asset_store()
    asset_store.load_texture(game.renderer, "tank", "./assets/chopper-spritesheet.png")

    # Create a entity builder
    entity_builder = game.create_entity()
    entity_builder.with_component(Position(100, 25))
    entity_builder.with_component(Velocity(10, 0))
    entity_builder.with_component(Sprite(32, 32, "tank"))

    entity_builder2 = game.create_entity()
    entity_builder2.with_component(Position(100, 50))
    entity_builder2.with_component(Velocity(23, 0))
    entity_builder2.with_component(Sprite(32, 32, "tank"))
    player = entity_builder.build()
    player2 = entity_builder2.build()
    game.add_system(MovementSystem)
    game.add_system(RenderSystem)

    def on_render():
        game.get_system(RenderSystem).update(
            game.delta_time, game.renderer, game.get_asset_store()
        )

    # We assign a lambda to the on_update event to call the update method of the MovementSystem
    game.on_update = lambda: game.get_system(MovementSystem).update(game.delta_time)
    game.on_render = on_render
    game.run()
