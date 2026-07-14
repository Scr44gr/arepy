"""A small, complete Arepy scene built with the ECS.

Move the bunny with WASD or the arrow keys, click to place it, and use the
mouse wheel to change its size.  Rendering scratch objects are allocated once
and then mutated so the frame loop does not create Vec2, Rect, or Color values.
"""

from pathlib import Path

from arepy import (
    ArepyEngine,
    Color,
    Input,
    Key,
    MouseButton,
    Rect,
    Renderer2D,
    SystemPipeline,
    Time,
    WindowFlag,
)
from arepy.asset_store import AssetStore
from arepy.bundle.components import RigidBody2D, Sprite, Transform
from arepy.ecs import Component, Entity, Query, With
from arepy.math import Vec2

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
PLAYFIELD_TOP = 104.0
PLAYFIELD_BOTTOM = 420.0
BUNNY_SIZE = 32
BUNNY_ASSET = "bunny.png"
BUNNY_PATH = Path(__file__).resolve().parent / "assets" / BUNNY_ASSET

MIN_SCALE = 1.5
MAX_SCALE = 5.0
SCALE_STEP = 0.25
DIAGONAL_NORMALIZER = 2.0**-0.5

WHITE = Color(255, 255, 255, 255)
BACKGROUND_TOP = Color(17, 23, 43, 255)
BACKGROUND_BOTTOM = Color(35, 48, 78, 255)
PANEL = Color(13, 18, 34, 230)
PANEL_OUTLINE = Color(98, 119, 181, 255)
ACCENT = Color(125, 211, 252, 255)
TEXT = Color(240, 245, 255, 255)
MUTED = Color(164, 176, 203, 255)
SHADOW = Color(4, 7, 15, 100)
TEXTURE_ORIGIN = (0.0, 0.0)


class PlayerControls(Component):
    """Data that belongs to the player-controlled entity."""

    def __init__(self, speed: float) -> None:
        super().__init__()
        self.speed = speed


class RenderScratch:
    """Mutable drawing values reused on every frame."""

    __slots__ = ("background", "hud", "source", "destination", "shadow")

    def __init__(self) -> None:
        self.background = Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.hud = Rect(24, WINDOW_HEIGHT - 96, WINDOW_WIDTH - 48, 72)
        self.source = Rect(0, 0, BUNNY_SIZE, BUNNY_SIZE)
        self.destination = Rect(0, 0, BUNNY_SIZE, BUNNY_SIZE)
        self.shadow = Rect(0, 0, BUNNY_SIZE, BUNNY_SIZE)


def control_player(
    query: Query[Entity, With[Transform, RigidBody2D, PlayerControls]],
    input_device: Input,
) -> None:
    """Translate input into reusable velocity and transform data."""

    components = next(
        query.iter_components(Transform, RigidBody2D, PlayerControls),
        None,
    )
    if components is None:
        return

    transform, rigid_body, controls = components
    move_x = int(
        input_device.is_key_down(Key.D) or input_device.is_key_down(Key.RIGHT)
    ) - int(input_device.is_key_down(Key.A) or input_device.is_key_down(Key.LEFT))
    move_y = int(
        input_device.is_key_down(Key.S) or input_device.is_key_down(Key.DOWN)
    ) - int(input_device.is_key_down(Key.W) or input_device.is_key_down(Key.UP))

    if move_x != 0 and move_y != 0:
        movement_scale = DIAGONAL_NORMALIZER
    else:
        movement_scale = 1.0

    velocity = rigid_body.velocity
    velocity.x = move_x * controls.speed * movement_scale
    velocity.y = move_y * controls.speed * movement_scale

    wheel = input_device.get_mouse_wheel_delta()
    if wheel != 0.0:
        scale = max(MIN_SCALE, min(MAX_SCALE, transform.scale.x + wheel * SCALE_STEP))
        transform.scale.x = scale
        transform.scale.y = scale

    sprite_size = BUNNY_SIZE * transform.scale.x
    if input_device.is_mouse_button_pressed(MouseButton.LEFT):
        mouse_x, mouse_y = input_device.get_mouse_position()
        position = transform.position
        position.x = mouse_x - sprite_size * 0.5
        position.y = mouse_y - sprite_size * 0.5


def move_player(
    query: Query[Entity, With[Transform, RigidBody2D]],
    time: Time,
) -> None:
    """Advance existing vectors during UPDATE without allocating replacements."""

    components = next(query.iter_components(Transform, RigidBody2D), None)
    if components is None:
        return

    transform, rigid_body = components
    position = transform.position
    velocity = rigid_body.velocity
    position.x += velocity.x * time.delta_seconds
    position.y += velocity.y * time.delta_seconds

    sprite_size = BUNNY_SIZE * transform.scale.x
    position.x = max(0.0, min(WINDOW_WIDTH - sprite_size, position.x))
    position.y = max(
        PLAYFIELD_TOP,
        min(PLAYFIELD_BOTTOM - sprite_size, position.y),
    )


def render_scene(
    query: Query[Entity, With[Transform, Sprite]],
    renderer: Renderer2D,
    assets: AssetStore,
    scratch: RenderScratch,
) -> None:
    """Draw the current ECS state without allocating drawing value objects."""

    renderer.start_frame()
    renderer.draw_rectangle_gradient_v(
        scratch.background,
        BACKGROUND_TOP,
        BACKGROUND_BOTTOM,
    )

    renderer.draw_text("AREPY - YOUR FIRST ECS SCENE", (28, 24), 28, TEXT)
    renderer.draw_text(
        "One entity, four components, three systems.",
        (30, 62),
        18,
        MUTED,
    )

    components = next(query.iter_components(Transform, Sprite), None)
    if components is not None:
        transform, sprite = components
        sprite_size = int(BUNNY_SIZE * transform.scale.x)

        destination = scratch.destination
        destination.x = transform.position.x
        destination.y = transform.position.y
        destination.width = sprite_size
        destination.height = sprite_size

        shadow = scratch.shadow
        shadow.x = destination.x + 8
        shadow.y = destination.y + 10
        shadow.width = sprite_size
        shadow.height = sprite_size

        renderer.draw_rectangle_rounded(shadow, 0.28, 8, SHADOW)
        renderer.draw_texture_ex(
            assets.get_texture(sprite.asset_id),
            scratch.source,
            destination,
            TEXTURE_ORIGIN,
            transform.rotation,
            WHITE,
        )

    renderer.draw_rectangle_rounded(scratch.hud, 0.18, 10, PANEL)
    renderer.draw_rectangle_rounded_lines(
        scratch.hud,
        0.18,
        10,
        PANEL_OUTLINE,
    )
    renderer.draw_text("MOVE", (48, 466), 16, ACCENT)
    renderer.draw_text("WASD / arrow keys", (48, 490), 18, TEXT)
    renderer.draw_text("PLACE", (330, 466), 16, ACCENT)
    renderer.draw_text("left click", (330, 490), 18, TEXT)
    renderer.draw_text("SCALE", (550, 466), 16, ACCENT)
    renderer.draw_text("mouse wheel", (550, 490), 18, TEXT)
    renderer.draw_fps((814, 486))
    renderer.end_frame()


def main() -> None:
    game = ArepyEngine(
        title="Arepy - Getting Started",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        max_frame_rate=0,
        window_flags=WindowFlag.VSYNC_HINT,
    )
    world = game.create_world("getting_started")

    assets = game.get_asset_store()
    assets.load_texture(
        game.renderer_2d,
        BUNNY_ASSET,
        str(BUNNY_PATH),
    )

    @world.on_shutdown
    def unload_assets() -> None:
        assets.unload_texture(game.renderer_2d, BUNNY_ASSET)

    world.add_resource(RenderScratch())

    (
        world.create_entity()
        .with_component(
            Transform(
                position=Vec2(432.0, 190.0),
                scale=Vec2(3.0, 3.0),
            )
        )
        .with_component(
            Sprite(
                asset_id=BUNNY_ASSET,
                src_rect=(0, 0, BUNNY_SIZE, BUNNY_SIZE),
                z_index=1,
            )
        )
        .with_component(RigidBody2D(velocity=Vec2(0.0, 0.0)))
        .with_component(PlayerControls(speed=280.0))
        .build()
    )

    world.add_system(SystemPipeline.INPUT, control_player)
    world.add_system(SystemPipeline.UPDATE, move_player)
    world.add_system(SystemPipeline.RENDER, render_scene)
    game.set_current_world("getting_started")
    game.run()


if __name__ == "__main__":
    main()
