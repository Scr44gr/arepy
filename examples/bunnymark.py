import random

from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline
from arepy.bundle.components.rigidbody import RigidBody2D
from arepy.bundle.components.sprite import Sprite
from arepy.bundle.components.transform import Transform
from arepy.ecs import Entities, Query, With
from arepy.ecs.world import World
from arepy.math import Vec2

WHITE_COLOR = Color(255, 255, 255, 255)
BUNNY_ASSET = "bunny.png"

BUNNY_COUNT = 5000
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D
) -> None:
    """Simple movement system"""
    delta_time: float = renderer.get_delta_time()
    sprite_size: int = 16

    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        rigidbody = entity.get_component(RigidBody2D)

        # Update position
        transform.position.x += rigidbody.velocity.x * delta_time
        transform.position.y += rigidbody.velocity.y * delta_time

        # Bounce logic with minimal conditions
        if transform.position.x <= 0:
            transform.position.x = 0
            rigidbody.velocity.x = abs(rigidbody.velocity.x)
        elif transform.position.x >= WINDOW_WIDTH - sprite_size:
            transform.position.x = WINDOW_WIDTH - sprite_size
            rigidbody.velocity.x = -abs(rigidbody.velocity.x)

        if transform.position.y <= 0:
            transform.position.y = 0
            rigidbody.velocity.y = abs(rigidbody.velocity.y)
        elif transform.position.y >= WINDOW_HEIGHT - sprite_size:
            transform.position.y = WINDOW_HEIGHT - sprite_size
            rigidbody.velocity.y = -abs(rigidbody.velocity.y)


def render_system(
    query: Query[Entities, With[Transform, Sprite]],
    renderer: Renderer2D,
    game: ArepyEngine,
):
    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    texture = game.get_asset_store().get_texture(BUNNY_ASSET)
    number_of_entities: int = 0
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        renderer.draw_texture_ex(
            texture,
            Rect(0, 0, 32, 32),
            Rect(transform.position.x, transform.position.y, 32, 32),
            (transform.origin.x, transform.origin.y),
            0.0,  # rotation
            WHITE_COLOR,
        )
        number_of_entities += 1
    renderer.draw_text(
        f"Entities: {number_of_entities}",
        (10, 30),
        font_size=20,
        color=Color(0, 0, 0, 255),
    )
    renderer.draw_fps((10, 10))
    renderer.end_frame()


def spawn_bunnies(world: World, count: int) -> None:
    for _ in range(count):
        x: float = random.uniform(0, WINDOW_WIDTH - 32)
        y: float = random.uniform(0, WINDOW_HEIGHT - 32)
        vx: float = random.uniform(-200, 200)
        vy: float = random.uniform(-200, 200)
        world.create_entity().with_component(
            Transform(position=Vec2(x, y), origin=Vec2(16, 16))
        ).with_component(RigidBody2D(velocity=Vec2(vx, vy))).with_component(
            Sprite(asset_id=BUNNY_ASSET, src_rect=(0, 0, 32, 32), z_index=1)
        ).build()


def main() -> None:
    game: ArepyEngine = ArepyEngine()
    game.title = "Arepy BunnyMark"
    game.window_width = WINDOW_WIDTH
    game.window_height = WINDOW_HEIGHT
    game.max_frame_rate = 0  # Unlimited
    game.init()
    world: World = game.create_world("bunnymark")
    asset_store = game.get_asset_store()
    renderer = game.renderer_2d
    asset_store.load_texture(renderer, BUNNY_ASSET, f"./assets/{BUNNY_ASSET}")
    spawn_bunnies(world, BUNNY_COUNT)
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    game.set_current_world("bunnymark")
    game.run()


if __name__ == "__main__":
    main()
