import random
from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray

from arepy import ArepyEngine, Color, Renderer2D, SystemPipeline
from arepy.bundle.components.rigidbody import RigidBody2D
from arepy.bundle.components.sprite import Sprite
from arepy.bundle.components.transform import Transform
from arepy.ecs import BatchQuery
from arepy.ecs.world import World
from arepy.engine.renderer.texture_atlas import TextureBatchPlan
from arepy.math import Vec2

WHITE_COLOR = Color(255, 255, 255, 255)
BUNNY_ASSET = "bunny.png"

BUNNY_COUNT = 8000
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480


@dataclass(slots=True)
class BunnyBatchState:
    position_x: NDArray[np.float64] | None = None
    position_y: NDArray[np.float64] | None = None
    plan: TextureBatchPlan | None = None


def movement_system(
    batch: BatchQuery[Transform, RigidBody2D],
    renderer: Renderer2D,
    batch_state: BunnyBatchState,
) -> None:
    """Simple movement system using the experimental BatchQuery path."""
    delta_time: float = renderer.get_delta_time()
    sprite_size: int = 16
    position = batch.vec2(Transform, "position")
    velocity = batch.vec2(RigidBody2D, "velocity")
    batch_state.position_x = position.x
    batch_state.position_y = position.y

    position.x += velocity.x * delta_time
    position.y += velocity.y * delta_time

    left = position.x <= 0
    right = position.x >= WINDOW_WIDTH - sprite_size
    top = position.y <= 0
    bottom = position.y >= WINDOW_HEIGHT - sprite_size

    position.x[left] = 0
    velocity.x[left] = abs(velocity.x[left])

    position.x[right] = WINDOW_WIDTH - sprite_size
    velocity.x[right] = -abs(velocity.x[right])

    position.y[top] = 0
    velocity.y[top] = abs(velocity.y[top])

    position.y[bottom] = WINDOW_HEIGHT - sprite_size
    velocity.y[bottom] = -abs(velocity.y[bottom])


def render_system(
    batch: BatchQuery[Sprite],
    renderer: Renderer2D,
    game: ArepyEngine,
    batch_state: BunnyBatchState,
) -> None:
    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    asset_store = game.get_asset_store()
    texture_atlas = asset_store.get_texture_atlas()
    if texture_atlas is None or not texture_atlas.atlases:
        raise RuntimeError("BunnyMark batch rendering requires a built texture atlas.")
    if batch_state.position_x is None or batch_state.position_y is None:
        raise RuntimeError(
            "BunnyMark batch rendering requires movement_system to publish position views."
        )

    sprites = cast(list[Sprite], batch.components(Sprite))
    batch_plan = batch_state.plan
    if batch_plan is None:
        batch_plan = texture_atlas.get_batch_plan(sprites)
        batch_state.plan = batch_plan
    renderer.draw_texture_batch(
        texture_atlas,
        batch_plan,
        batch_state.position_x,
        batch_state.position_y,
        WHITE_COLOR,
    )

    renderer.draw_text(
        f"Entities: {len(sprites)}",
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
    asset_store.build_texture_atlas(renderer)
    world.add_resource(BunnyBatchState())
    spawn_bunnies(world, BUNNY_COUNT)
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    game.set_current_world("bunnymark")
    game.run()


if __name__ == "__main__":
    main()
