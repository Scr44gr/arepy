import random
from collections import deque
from typing import cast

from arepy_ecs import Component, Entities, Entity, Query, With

from arepy import ArepyEngine, Color, Renderer2D, SystemPipeline, Time, Timers, World
from arepy.bundle.components._field_views import InternedStringTable
from arepy.bundle.components.rigidbody import RigidBody2D
from arepy.bundle.components.transform import Transform
from arepy.math import Vec2

WIDTH = 960
HEIGHT = 540
MAX_LETTERS = 120
BACKGROUND = Color(16, 18, 30, 255)
TEXT = Color(238, 241, 255, 255)
PALETTE = [
    Color(255, 99, 132, 255),
    Color(255, 206, 86, 255),
    Color(75, 192, 192, 255),
    Color(54, 162, 235, 255),
    Color(153, 102, 255, 255),
]

_GLYPHS = InternedStringTable()


class Letter(Component):
    glyph_handle: int = 0
    size: int = 0
    color_r: int = 255
    color_g: int = 255
    color_b: int = 255
    color_a: int = 255


def make_letter(glyph: str, size: int, color: Color) -> Letter:
    return Letter(
        glyph_handle=_GLYPHS.intern(glyph),
        size=size,
        color_r=color.r,
        color_g=color.g,
        color_b=color.b,
        color_a=color.a,
    )


def resolve_letter_glyph(letter: Letter) -> str:
    return cast(str, _GLYPHS.resolve(letter.glyph_handle))


def resolve_letter_color(letter: Letter) -> Color:
    return Color(letter.color_r, letter.color_g, letter.color_b, letter.color_a)


def add_letter(
    world: World,
    letters: deque[Entity],
    glyph: str,
    position: Vec2,
    velocity: Vec2,
    size: int,
    color: Color,
) -> None:
    if len(letters) >= MAX_LETTERS:
        letters.popleft().kill()

    entity = (
        world.create_entity()
        .with_component(Transform(position_x=position.x, position_y=position.y))
        .with_component(RigidBody2D(velocity_x=velocity.x, velocity_y=velocity.y))
        .with_component(make_letter(glyph, size, color))
        .build()
    )
    letters.append(entity)


def rain_letter(world: World, letters: deque[Entity]) -> None:
    size = random.choice((24, 32, 40))
    add_letter(
        world,
        letters,
        random.choice("AREPYTIMER"),
        Vec2(random.uniform(20, WIDTH - 60), -size),
        Vec2(random.uniform(-160, 160), random.uniform(-40, 80)),
        size,
        random.choice(PALETTE),
    )


def burst_word(world: World, letters: deque[Entity], word: str) -> None:
    start_x = WIDTH * 0.5 - len(word) * 18
    for index, glyph in enumerate(word):
        add_letter(
            world,
            letters,
            glyph,
            Vec2(start_x + index * 36, 40),
            Vec2(random.uniform(-80, 80), random.uniform(-420, -260)),
            36,
            random.choice(PALETTE),
        )


def physics_system(
    query: Query[Entities, With[Transform, RigidBody2D, Letter]],
    time: Time,
) -> None:
    dt = time.delta_seconds
    for transform, rigidbody, letter in query.iter_components(
        Transform,
        RigidBody2D,
        Letter,
    ):
        rigidbody.velocity_y += 900 * dt
        transform.position_x += rigidbody.velocity_x * dt
        transform.position_y += rigidbody.velocity_y * dt

        max_x = WIDTH - letter.size
        max_y = HEIGHT - letter.size - 12

        if transform.position_x < 0:
            transform.position_x = 0
            rigidbody.velocity_x = abs(rigidbody.velocity_x)
        elif transform.position_x > max_x:
            transform.position_x = max_x
            rigidbody.velocity_x = -abs(rigidbody.velocity_x)

        if transform.position_y < 0:
            transform.position_y = 0
            rigidbody.velocity_y = abs(rigidbody.velocity_y) * 0.5
        elif transform.position_y > max_y:
            transform.position_y = max_y
            rigidbody.velocity_y = -max(120.0, abs(rigidbody.velocity_y) * 0.72)
            rigidbody.velocity_x *= 0.98


def render_system(
    query: Query[Entities, With[Transform, Letter]],
    renderer: Renderer2D,
    time: Time,
) -> None:
    renderer.start_frame()
    renderer.clear(BACKGROUND)

    count = 0
    for transform, letter in query.iter_components(Transform, Letter):
        renderer.draw_text(
            resolve_letter_glyph(letter),
            (transform.position_x, transform.position_y),
            letter.size,
            resolve_letter_color(letter),
        )
        count += 1

    renderer.draw_text("timers raining letters", (18, 18), 26, TEXT)
    renderer.draw_text(
        f"letters: {count}  time: {time.elapsed_seconds:.1f}s",
        (18, 50),
        18,
        TEXT,
    )
    renderer.draw_fps((18, HEIGHT - 28))
    renderer.end_frame()


def main() -> None:
    game = ArepyEngine(
        title="Arepy Timer Letters",
        width=WIDTH,
        height=HEIGHT,
        max_frame_rate=0,
    )
    world = game.create_world("timer_letters")
    letters: deque[Entity] = deque()

    @world.on_startup
    def start() -> None:
        for entity in letters:
            entity.kill()
        letters.clear()
        timers = world.get_world_resource(Timers)
        timers.clear()
        timers.every(0.08, lambda: rain_letter(world, letters))
        timers.every(1.8, lambda: burst_word(world, letters, "AREPY"))

    world.add_system(SystemPipeline.UPDATE, physics_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    game.set_current_world("timer_letters")
    game.run()


if __name__ == "__main__":
    main()
