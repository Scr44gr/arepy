import random
from typing import Protocol, cast

import numpy as np
from arepy_ecs import Entity, Query, With, World
from numpy.typing import NDArray

from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline
from arepy.bundle.components.rigidbody import RigidBody2D
from arepy.bundle.components.sprite import Sprite
from arepy.bundle.components.transform import Transform
from arepy.math import Vec2

WHITE_COLOR = Color(255, 255, 255, 255)
BUNNY_ASSET = "bunny.png"

BUNNY_COUNT = 5000
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

FloatBatch = NDArray[np.float32]
BoolBatch = NDArray[np.bool_]


class TransformBatch(Protocol):
    position_x: FloatBatch
    position_y: FloatBatch


class RigidBody2DBatch(Protocol):
    velocity_x: FloatBatch
    velocity_y: FloatBatch


def movement_system(
    query: Query[Entity, With[Transform, RigidBody2D]],
    renderer: Renderer2D,
) -> None:
    """Simple movement system using the arepy-ecs batch result path."""
    delta_time: float = renderer.get_delta_time()
    sprite_size: int = 16
    transforms, rigidbodies = cast(
        tuple[TransformBatch, RigidBody2DBatch],
        query.result(Transform, RigidBody2D),
    )
    position_x = transforms.position_x
    position_y = transforms.position_y
    velocity_x = rigidbodies.velocity_x
    velocity_y = rigidbodies.velocity_y

    position_x += velocity_x * delta_time
    position_y += velocity_y * delta_time

    left: BoolBatch = position_x <= 0
    right: BoolBatch = position_x >= WINDOW_WIDTH - sprite_size
    top: BoolBatch = position_y <= 0
    bottom: BoolBatch = position_y >= WINDOW_HEIGHT - sprite_size

    position_x[left] = 0
    velocity_x[left] = np.abs(velocity_x[left])

    position_x[right] = WINDOW_WIDTH - sprite_size
    velocity_x[right] = -np.abs(velocity_x[right])

    position_y[top] = 0
    velocity_y[top] = np.abs(velocity_y[top])

    position_y[bottom] = WINDOW_HEIGHT - sprite_size
    velocity_y[bottom] = -np.abs(velocity_y[bottom])


def render_system(
    query: Query[Entity, With[Transform, Sprite]],
    renderer: Renderer2D,
    game: ArepyEngine,
):
    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    texture = game.get_asset_store().get_texture(BUNNY_ASSET)
    number_of_entities: int = 0
    for (transform,) in query.iter_components(Transform):
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
    game: ArepyEngine = ArepyEngine(
        title="Arepy BunnyMark",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        max_frame_rate=0,
    )
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
