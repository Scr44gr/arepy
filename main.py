import OpenGL.GL as gl
import sdl2
from glm import vec2

from arepy import Arepy
from arepy.arepy_imgui import imgui
from arepy.asset_store import AssetStore
from arepy.ecs import Component, System
from arepy.engine.renderer import BaseRenderer


class Transform(Component):
    def __init__(
        self, position: vec2 = vec2(0, 0), scale: vec2 = vec2(1, 1), rotation: float = 0
    ):
        self.position = position
        self.scale = scale
        self.rotation = rotation


class Rigidbody(Component):
    def __init__(self, velocity: vec2 = vec2(0, 0), mass: float = 1):
        self.velocity = velocity
        self.mass = mass


class Collider(Component):
    def __init__(self, width, height, offset, is_colliding=False):
        self.width = width
        self.height = height
        self.offset = offset
        self.is_colliding = is_colliding


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
        self.require_components([Transform, Rigidbody])

    def update(self, dt: float):
        for entity in self.get_entities():
            position = entity.get_component(Transform).position
            velocity = entity.get_component(Rigidbody).velocity
            position.x += velocity.x * dt
            position.y += velocity.y * dt


class CollisionSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Transform, Collider])

    def update(self, dt: float):
        for entity in self.get_entities():
            position = entity.get_component(Transform).position
            collision_box = entity.get_component(Collider)
            collision_offset = collision_box.offset

            for other_entity in self.get_entities():
                if other_entity != entity:
                    other_position = other_entity.get_component(Transform).position
                    other_collision_box = other_entity.get_component(Collider)
                    other_collision_offset = other_collision_box.offset

                    if (
                        position.x + collision_box.width + collision_offset
                        >= other_position.x + other_collision_offset
                        and position.x + collision_offset
                        <= other_position.x + other_collision_box.width
                        and position.y + collision_box.height + collision_offset
                        >= other_position.y + other_collision_offset
                        and position.y + collision_offset
                        <= other_position.y + other_collision_box.height
                    ):
                        collision_box.is_colliding = True
                    else:
                        collision_box.is_colliding = False


class RenderCollisionBoxSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Transform, Collider])

    def update(self, dt: float, renderer: BaseRenderer):
        for entity in self.get_entities():
            position = entity.get_component(Transform).position
            collision_box = entity.get_component(Collider)

            colliding_color = (
                (0, 255, 0, 255) if collision_box.is_colliding else (255, 0, 0, 255)
            )

            # renderer.draw_rect(
            #    position.x,
            #    position.y,
            #    collision_box.width,
            #    collision_box.height,
            #    colliding_color,
            # )
            ## draw a circle
            # renderer.draw_circle(position.x, position.y, 32, (255, 255, 255, 255))


class RenderSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Transform, Sprite])

    def update(
        self,
        dt: float,
        renderer: BaseRenderer,
        asset_store: AssetStore,
    ):
        tick = sdl2.SDL_GetTicks()
        imgui.begin("Debug1 ")
        imgui.text("FPS: " + str(1 // dt))

        imgui.end()
        for entity in self.get_entities():
            position = entity.get_component(Transform).position
            sprite = entity.get_component(Sprite)
            texture_id = asset_store.get_texture(sprite.asset_id)
            # testing animation

            renderer.draw_sprite(
                texture_id,
                (position.x, position.y),
                (sprite.width, sprite.height),
                color=(255, 255, 255, 255),
            )


def stress_entities(game: Arepy):
    from random import randint

    for i in range(400):
        entity_builder = game.create_entity()
        entity_builder.with_component(
            Transform(position=vec2(randint(0, 640), randint(0, 480)))
        )
        entity_builder.with_component(Rigidbody(velocity=vec2(100, 0)))
        entity_builder.with_component(Sprite(32, 32, "tank"))
        entity_builder.build()


if __name__ == "__main__":
    game = Arepy()
    game.init()
    game.title = "My awesome game"
    game.debug = True
    # load assets
    asset_store = game.get_asset_store()
    asset_store.load_texture(game.renderer, "tank", "./assets/tank.png")

    # Create a entity builder
    stress_entities(game)
    game.add_system(MovementSystem)
    game.add_system(RenderSystem)
    game.add_system(RenderCollisionBoxSystem)
    game.add_system(CollisionSystem)

    def on_render():
        game.get_system(RenderSystem).update(
            game.delta_time,
            game.renderer,
            game.get_asset_store(),
        )
        game.get_system(RenderCollisionBoxSystem).update(game.delta_time, game.renderer)

    def on_update():
        game.get_system(MovementSystem).update(game.delta_time)
        game.get_system(CollisionSystem).update(game.delta_time)

    # We assign a lambda to the on_update event to call the update method of the MovementSystem
    game.on_update = on_update
    game.on_render = on_render
    game.run()
