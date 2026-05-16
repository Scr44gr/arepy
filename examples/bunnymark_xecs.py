from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import xecs as xx
from xecs.xecs import RustApp

from arepy import ArepyEngine, Color, Rect

WHITE_COLOR = Color(255, 255, 255, 255)
BLACK_COLOR = Color(0, 0, 0, 255)
BUNNY_ASSET = "bunny.png"

BUNNY_COUNT = 50000
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
SPRITE_SIZE = 16.0


class Velocity(xx.Component):
    value: xx.Vec2


@dataclass(slots=True)
class XecsBunnyWorld:
    transforms: xx.Transform2
    velocities: Velocity
    bunny_count: int


def _add_pool(
    world: xx.World,
    rust_app: RustApp,
    component_type: type[xx.Component],
    capacity: int,
) -> None:
    pool = component_type.create_pool(capacity)
    component_id = xx.Component.component_ids[component_type]
    rust_app.add_pool(component_id, pool.p_capacity)
    world.add_pool(pool)


def create_bunny_world(
    bunny_count: int = BUNNY_COUNT,
    *,
    seed: int = 7,
) -> XecsBunnyWorld:
    world = xx.World()
    rust_app = RustApp(num_pools=len(xx.Component.component_ids), num_queries=0)

    _add_pool(world, rust_app, xx.Transform2, bunny_count)
    _add_pool(world, rust_app, Velocity, bunny_count)

    commands = xx.Commands.p_new(rust_app, world)
    transform_indices, velocity_indices = commands.spawn(
        (xx.Transform2, Velocity),
        bunny_count,
    )

    transforms = world.get_view(xx.Transform2, transform_indices)
    velocities = world.get_view(Velocity, velocity_indices)

    generator = np.random.default_rng(seed)
    transforms.translation.x.fill(
        generator.random(bunny_count, dtype=np.float32) * (WINDOW_WIDTH - SPRITE_SIZE)
    )
    transforms.translation.y.fill(
        generator.random(bunny_count, dtype=np.float32) * (WINDOW_HEIGHT - SPRITE_SIZE)
    )
    velocities.value.x.fill(
        generator.uniform(-200.0, 200.0, bunny_count).astype(np.float32)
    )
    velocities.value.y.fill(
        generator.uniform(-200.0, 200.0, bunny_count).astype(np.float32)
    )

    return XecsBunnyWorld(transforms, velocities, bunny_count)


def update_bunnies(state: XecsBunnyWorld, delta_seconds: float) -> None:
    transform = state.transforms
    velocity = state.velocities

    transform.translation += velocity.value * delta_seconds

    left = transform.translation.x <= 0
    right = transform.translation.x >= WINDOW_WIDTH - SPRITE_SIZE
    top = transform.translation.y <= 0
    bottom = transform.translation.y >= WINDOW_HEIGHT - SPRITE_SIZE

    transform.translation.x[left].fill(0)
    velocity.value.x[left] *= -1

    transform.translation.x[right].fill(WINDOW_WIDTH - SPRITE_SIZE)
    velocity.value.x[right] *= -1

    transform.translation.y[top].fill(0)
    velocity.value.y[top] *= -1

    transform.translation.y[bottom].fill(WINDOW_HEIGHT - SPRITE_SIZE)
    velocity.value.y[bottom] *= -1


def render_bunnies(
    state: XecsBunnyWorld,
    game: ArepyEngine,
    update_duration_ms: float,
) -> None:
    renderer = game.renderer_2d
    texture = game.get_asset_store().get_texture(BUNNY_ASSET)
    transforms = state.transforms
    positions_x = transforms.translation.x.numpy()
    positions_y = transforms.translation.y.numpy()

    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    for x, y in zip(positions_x, positions_y, strict=True):
        renderer.draw_texture(
            texture,
            Rect(0, 0, 32, 32),
            Rect(float(x), float(y), 32, 32),
            color=WHITE_COLOR,
        )
    renderer.draw_text(
        f"Entities: {state.bunny_count}",
        (10, 30),
        font_size=20,
        color=BLACK_COLOR,
    )
    renderer.draw_text(
        f"update_bunnies: {update_duration_ms:.3f} ms",
        (10, 50),
        font_size=20,
        color=BLACK_COLOR,
    )
    renderer.draw_fps((10, 10))
    renderer.end_frame()
    renderer.swap_buffers()


def main() -> None:
    game = ArepyEngine(
        title="Arepy BunnyMark (xecs)",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        max_frame_rate=0,
    )
    asset_path = Path(__file__).with_name("assets") / BUNNY_ASSET
    game.get_asset_store().load_texture(
        game.renderer_2d,
        BUNNY_ASSET,
        str(asset_path),
    )

    state = create_bunny_world(BUNNY_COUNT)

    while not game.display.window_should_close():
        started = perf_counter()
        update_bunnies(state, game.renderer_2d.get_delta_time())
        update_duration_ms = (perf_counter() - started) * 1000.0
        render_bunnies(state, game, update_duration_ms)


if __name__ == "__main__":
    main()
