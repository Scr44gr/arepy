import random
from typing import cast

import numpy as np
from arepy_ecs import Component, Entity, Query, With, World
from numpy.typing import NDArray

from arepy import ArepyEngine, Color, Rect, SystemPipeline

WHITE_COLOR = Color(255, 255, 255, 255)
BUNNY_ASSET = "bunny.png"

BUNNY_COUNT = 5000
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
SPRITE_SIZE = 32
SPRITE_ORIGIN = 16.0
SPRITE_SOURCE_RECT = Rect(0, 0, SPRITE_SIZE, SPRITE_SIZE)

FloatArray = NDArray[np.float32]
BoolArray = NDArray[np.bool_]


class Position(Component):
    x: float = 0.0
    y: float = 0.0


class Velocity(Component):
    x: float = 0.0
    y: float = 0.0


def movement_system(
    query: Query[Entity, With[Position, Velocity]],
    game: ArepyEngine,
) -> None:
    delta_time = game.renderer_2d.get_delta_time()
    position, velocity = query.result(Position, Velocity)

    positions_x = cast(FloatArray, position.x)
    positions_y = cast(FloatArray, position.y)
    velocity_x = cast(FloatArray, velocity.x)
    velocity_y = cast(FloatArray, velocity.y)

    positions_x += velocity_x * delta_time
    positions_y += velocity_y * delta_time

    left: BoolArray = positions_x <= 0
    right: BoolArray = positions_x >= WINDOW_WIDTH - SPRITE_SIZE
    top: BoolArray = positions_y <= 0
    bottom: BoolArray = positions_y >= WINDOW_HEIGHT - SPRITE_SIZE

    positions_x[left] = 0
    velocity_x[left] = np.abs(velocity_x[left])

    positions_x[right] = WINDOW_WIDTH - SPRITE_SIZE
    velocity_x[right] = -np.abs(velocity_x[right])

    positions_y[top] = 0
    velocity_y[top] = np.abs(velocity_y[top])

    positions_y[bottom] = WINDOW_HEIGHT - SPRITE_SIZE
    velocity_y[bottom] = -np.abs(velocity_y[bottom])


def render_system(
    query: Query[Entity, With[Position]],
    game: ArepyEngine,
):
    renderer = game.renderer_2d
    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    texture = game.get_asset_store().get_texture(BUNNY_ASSET)
    number_of_entities = 0
    for (position,) in query.iter_components(Position):
        renderer.draw_texture_ex(
            texture,
            SPRITE_SOURCE_RECT,
            Rect(position.x, position.y, SPRITE_SIZE, SPRITE_SIZE),
            (SPRITE_ORIGIN, SPRITE_ORIGIN),
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
        x: float = random.uniform(0, WINDOW_WIDTH - SPRITE_SIZE)
        y: float = random.uniform(0, WINDOW_HEIGHT - SPRITE_SIZE)
        vx: float = random.uniform(-200, 200)
        vy: float = random.uniform(-200, 200)
        world.create_entity().with_component(Position(x=x, y=y)).with_component(
            Velocity(x=vx, y=vy)
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
