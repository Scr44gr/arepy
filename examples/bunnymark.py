import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline
from arepy.bundle.components.rigidbody import RigidBody2D
from arepy.bundle.components.sprite import Sprite
from arepy.bundle.components.transform import Transform
from arepy.ecs import BatchQuery
from arepy.ecs.world import World
from arepy.engine.renderer.texture_atlas import TextureBatchLayout
from arepy.math import Vec2

WHITE_COLOR = Color(255, 255, 255, 255)
HUD_COLOR = Color(14, 20, 34, 235)
HUD_TEXT_COLOR = Color(238, 244, 255, 255)
HUD_ACCENT_COLOR = Color(85, 225, 160, 255)
HUD_RECT = Rect(8, 8, 232, 68)
BUNNY_ASSET = "bunny.png"
BUNNY_PATH = Path(__file__).resolve().parent / "assets" / BUNNY_ASSET

BUNNY_COUNT = 50_000
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
SPRITE_SIZE = 16
MAX_BUNNY_X = WINDOW_WIDTH - SPRITE_SIZE
MAX_BUNNY_Y = WINDOW_HEIGHT - SPRITE_SIZE


@dataclass(slots=True)
class BunnyBatchState:
    position_x: NDArray[np.float64] | None = None
    position_y: NDArray[np.float64] | None = None
    origin_x: NDArray[np.float64] | None = None
    origin_y: NDArray[np.float64] | None = None
    rotation: NDArray[np.float64] | None = None
    delta_scratch: NDArray[np.float64] | None = None
    boundary_mask: NDArray[np.bool_] | None = None
    layout: TextureBatchLayout | None = None


def movement_system(
    batch: BatchQuery[Transform, RigidBody2D],
    renderer: Renderer2D,
    batch_state: BunnyBatchState,
) -> None:
    """Move every bunny through the vectorized BatchQuery path."""
    delta_time: float = renderer.get_delta_time()
    position = batch.vec2(Transform, "position")
    velocity = batch.vec2(RigidBody2D, "velocity")
    position_storage_changed = (
        batch_state.position_x is not position.x
        or batch_state.position_y is not position.y
    )
    batch_state.position_x = position.x
    batch_state.position_y = position.y
    if (
        position_storage_changed
        or batch_state.origin_x is None
        or batch_state.origin_y is None
    ):
        origin = batch.vec2(Transform, "origin")
        batch_state.origin_x = origin.x
        batch_state.origin_y = origin.y
    if position_storage_changed or batch_state.rotation is None:
        batch_state.rotation = np.zeros_like(position.x)
    delta_scratch = batch_state.delta_scratch
    boundary_mask = batch_state.boundary_mask
    if delta_scratch is None or boundary_mask is None or position_storage_changed:
        delta_scratch = np.empty_like(position.x)
        boundary_mask = np.empty_like(position.x, dtype=np.bool_)
        batch_state.delta_scratch = delta_scratch
        batch_state.boundary_mask = boundary_mask

    np.multiply(velocity.x, delta_time, out=delta_scratch)
    np.add(position.x, delta_scratch, out=position.x)

    np.less_equal(position.x, 0.0, out=boundary_mask)
    np.copysign(velocity.x, 1.0, out=velocity.x, where=boundary_mask)

    np.greater_equal(position.x, MAX_BUNNY_X, out=boundary_mask)
    np.copysign(velocity.x, -1.0, out=velocity.x, where=boundary_mask)
    np.clip(position.x, 0.0, MAX_BUNNY_X, out=position.x)

    np.multiply(velocity.y, delta_time, out=delta_scratch)
    np.add(position.y, delta_scratch, out=position.y)

    np.less_equal(position.y, 0.0, out=boundary_mask)
    np.copysign(velocity.y, 1.0, out=velocity.y, where=boundary_mask)

    np.greater_equal(position.y, MAX_BUNNY_Y, out=boundary_mask)
    np.copysign(velocity.y, -1.0, out=velocity.y, where=boundary_mask)
    np.clip(position.y, 0.0, MAX_BUNNY_Y, out=position.y)


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
    if (
        batch_state.position_x is None
        or batch_state.position_y is None
        or batch_state.origin_x is None
        or batch_state.origin_y is None
        or batch_state.rotation is None
    ):
        raise RuntimeError(
            "BunnyMark batch rendering requires movement_system to publish DrawTexturePro views."
        )

    sprites = batch.components(Sprite)
    batch_layout = batch_state.layout
    if batch_layout is None:
        batch_layout = texture_atlas.get_batch_layout(sprites)
        batch_state.layout = batch_layout
    renderer.draw_texture_batch(
        texture_atlas,
        batch_layout,
        batch_state.position_x,
        batch_state.position_y,
        batch_layout.default_dest_width,
        batch_layout.default_dest_height,
        batch_state.origin_x,
        batch_state.origin_y,
        batch_state.rotation,
        WHITE_COLOR,
    )

    renderer.draw_rectangle_rounded(HUD_RECT, 0.18, 8, HUD_COLOR)
    renderer.draw_text("BUNNYMARK", (20, 16), 16, HUD_ACCENT_COLOR)
    renderer.draw_text(
        f"{len(sprites):,} entities  |  {renderer.get_framerate()} FPS",
        (20, 43),
        font_size=18,
        color=HUD_TEXT_COLOR,
    )
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
    asset_store.load_texture(renderer, BUNNY_ASSET, str(BUNNY_PATH))
    asset_store.build_texture_atlas(renderer)

    @world.on_shutdown
    def unload_assets() -> None:
        # unload_texture() also invalidates and releases the atlas first.
        asset_store.unload_texture(renderer, BUNNY_ASSET)

    world.add_resource(BunnyBatchState())
    spawn_bunnies(world, BUNNY_COUNT)
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    game.set_current_world("bunnymark")
    game.run()


if __name__ == "__main__":
    main()
