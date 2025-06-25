from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline
from arepy.bundle.components.rigidbody_component import RigidBody2D
from arepy.bundle.components.sprite_component import Sprite
from arepy.bundle.components.transform_component import Transform
from arepy.ecs import Entities, Query, With
from arepy.math import Vec2

WHITE_COLOR = Color(255, 255, 255, 255)
BUNNY_ASSET = "bunny.png"

BUNNY_COUNT = 3000  # You can increase this for stress testing


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D
):
    delta_time = renderer.get_delta_time()
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        velocity = entity.get_component(RigidBody2D).velocity
        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time
        # Bounce on window edges
        if transform.position.x < 0 or transform.position.x > 640 - 32:
            velocity.x = -velocity.x
        if transform.position.y < 0 or transform.position.y > 480 - 32:
            velocity.y = -velocity.y


def render_system(
    query: Query[Entities, With[Transform, Sprite]],
    renderer: Renderer2D,
    game: ArepyEngine,
):
    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    texture = game.get_asset_store().get_texture(BUNNY_ASSET)
    number_of_entities = 0
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        renderer.draw_texture_ex(
            texture,
            Rect(0, 0, 32, 32),
            Rect(transform.position.x, transform.position.y, 32, 32),
            (32 / 2, 32 / 2),
            0.0,  # rotation
            Color(255, number_of_entities % 255, 0, 255),  # color
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


def main():
    game = ArepyEngine()
    game.title = "Arepy BunnyMark"
    game.window_width = 640
    game.window_height = 480
    game.max_frame_rate = 0  # Unlimited
    game.init()
    world = game.create_world("bunnymark")
    asset_store = game.get_asset_store()
    renderer = game.renderer
    # Register asset_store as a resource for ECS injection
    asset_store.load_texture(renderer, BUNNY_ASSET, f"./assets/{BUNNY_ASSET}")
    import random

    for _ in range(BUNNY_COUNT):
        x = random.uniform(0, 640 - 32)
        y = random.uniform(0, 480 - 32)
        vx = random.uniform(-200, 200)
        vy = random.uniform(-200, 200)
        world.create_entity().with_component(
            Transform(position=Vec2(x, y))
        ).with_component(RigidBody2D(velocity=Vec2(vx, vy))).with_component(
            Sprite(asset_id=BUNNY_ASSET, src_rect=(0, 0, 32, 32), z_index=1)
        ).build()
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    game.set_current_world("bunnymark")
    game.run()


if __name__ == "__main__":
    main()
