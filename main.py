import OpenGL.GL as gl
import sdl2
from glm import vec2

from arepy import Arepy
from arepy.arepy_imgui import imgui
from arepy.asset_store import AssetStore
from arepy.ecs import Component, System
from arepy.engine.renderer import BaseRenderer


class Animation(Component):
    def __init__(
        self, frame_count: int, frame_speed_rate: float, current_frame=0, start_time=0
    ):
        self.frame_count = frame_count
        self.frame_speed_rate = frame_speed_rate
        self.start_time = start_time
        self.current_frame = current_frame


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
        src_rect: tuple[int, int],
        z_index: int,
    ):
        self.width = width
        self.height = height
        self.asset_id = asset_id
        self.src_rect: list = [width, height, src_rect[0], src_rect[1]]
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


class AnimationSystem(System):
    """System that handles animations."""

    def __init__(self) -> None:
        super().__init__()
        self.require_components([Animation, Sprite])

    def update(self, delta_time: float) -> None:
        """Update the animation component of all entities that have one."""
        for entity in self.get_entities():
            animation = entity.get_component(Animation)
            sprite = entity.get_component(Sprite)
            current_time = sdl2.SDL_GetTicks()

            animation.current_frame = int(
                (
                    (
                        (current_time - animation.start_time)
                        * animation.frame_speed_rate
                        / 1000
                    )
                    % animation.frame_count
                )
            )

            sprite.src_rect[2] = animation.current_frame * sprite.width


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
            texture = asset_store.get_texture(sprite.asset_id)
            texture_size = texture.get_size()
            dst_rect = (
                texture_size[0],
                texture_size[1],
                position.x,
                position.y,
            )
            src_rect = (
                float(sprite.src_rect[0]),
                float(sprite.src_rect[1]),
                float(sprite.src_rect[2]),
                float(sprite.src_rect[3]),
            )
            # draw a line

            renderer.draw_sprite(
                texture,
                src_rect,
                dst_rect,
                (255, 255, 255, 255),
                # rotate the sprite by tick
                angle=(tick / 1000) * 3.14 / 2 % 360,
            )


def spawn_entities(game: Arepy, number_of_entities: int):
    from random import randint

    for i in range(number_of_entities):
        entity_builder = game.create_entity()
        entity_builder.with_component(
            Transform(position=vec2(randint(0, 640), randint(0, 480)))
        )
        entity_builder.with_component(Rigidbody(velocity=vec2(randint(0, 100), 0)))
        entity_builder.with_component(Sprite(32, 32, "chopper", (0, 64), 0))
        entity_builder.with_component(Animation(2, 8))
        e = entity_builder.build()


if __name__ == "__main__":
    game = Arepy()
    game.init()
    game.title = "My awesome game"
    game.debug = True
    # load assets
    asset_store = game.get_asset_store()
    asset_store.load_texture(game.renderer, "chopper", "./assets/chopper.png")

    # Create a entity builder
    spawn_entities(game, 100)
    game.add_system(MovementSystem)
    game.add_system(RenderSystem)
    game.add_system(RenderCollisionBoxSystem)
    game.add_system(CollisionSystem)
    game.add_system(AnimationSystem)

    def on_render():
        game.get_system(RenderSystem).update(
            game.delta_time,
            game.renderer,
            game.get_asset_store(),
        )
        game.get_system(AnimationSystem).update(game.delta_time)

    def on_update():
        game.get_system(MovementSystem).update(game.delta_time)
        game.get_system(CollisionSystem).update(game.delta_time)

    # We assign a lambda to the on_update event to call the update method of the MovementSystem
    game.on_update = on_update
    game.on_render = on_render
    game.run()
