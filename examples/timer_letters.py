import random
from collections import deque
from numbers import Integral

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
    glyph_handle: int
    size: int
    color_r: int
    color_g: int
    color_b: int
    color_a: int

    def __init__(self, glyph: str, size: int, color: Color) -> None:
        super().__init__()
        self.glyph = glyph
        self.size = size
        self.color = color

    @property
    def glyph(self) -> object:
        return _GLYPHS.resolve(self.glyph_handle)

    @glyph.setter
    def glyph(self, value: str) -> None:
        self.glyph_handle = _GLYPHS.intern(value)

    @property
    def color(self) -> object:
        values = (self.color_r, self.color_g, self.color_b, self.color_a)
        if all(isinstance(value, Integral) for value in values):
            return Color(*(int(value) for value in values))
        return values

    @color.setter
    def color(self, value: Color) -> None:
        self.color_r = value.r
        self.color_g = value.g
        self.color_b = value.b
        self.color_a = value.a


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
        .with_component(Transform(position=position))
        .with_component(RigidBody2D(velocity=velocity))
        .with_component(Letter(glyph, size, color))
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
        rigidbody.velocity.y += 900 * dt
        transform.position.x += rigidbody.velocity.x * dt
        transform.position.y += rigidbody.velocity.y * dt

        max_x = WIDTH - letter.size
        max_y = HEIGHT - letter.size - 12

        if transform.position.x < 0:
            transform.position.x = 0
            rigidbody.velocity.x = abs(rigidbody.velocity.x)
        elif transform.position.x > max_x:
            transform.position.x = max_x
            rigidbody.velocity.x = -abs(rigidbody.velocity.x)

        if transform.position.y < 0:
            transform.position.y = 0
            rigidbody.velocity.y = abs(rigidbody.velocity.y) * 0.5
        elif transform.position.y > max_y:
            transform.position.y = max_y
            rigidbody.velocity.y = -max(120.0, abs(rigidbody.velocity.y) * 0.72)
            rigidbody.velocity.x *= 0.98


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
            letter.glyph,
            (transform.position.x, transform.position.y),
            letter.size,
            letter.color,
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
