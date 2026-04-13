from math import cos, pi

from arepy import (
    Animator,
    ArepyEngine,
    Color,
    Input,
    Key,
    Renderer2D,
    SystemPipeline,
    World,
)
from arepy.math import Vec2

WIDTH = 960
HEIGHT = 540
BACKGROUND = Color(18, 22, 30, 255)
TITLE = Color(240, 244, 255, 255)
SUBTITLE = Color(153, 166, 191, 255)
LETTER_SIZE = 72
LETTER_SPACING = 18.0
WORD = "AREPY"
PALETTE = [
    Color(255, 99, 132, 255),
    Color(255, 206, 86, 255),
    Color(75, 192, 192, 255),
    Color(54, 162, 235, 255),
    Color(153, 102, 255, 255),
]


class LetterState:
    def __init__(self, glyph: str, rest_position: Vec2, base_color: Color) -> None:
        self.glyph = glyph
        self.rest_position = rest_position
        self.base_color = base_color
        self.position = rest_position.copy()
        self.size = LETTER_SIZE
        self.color = base_color
        self.shadow_offset = Vec2(8.0, 10.0)
        self.shadow_color = Color(7, 10, 18, 120)


def with_alpha(color: Color, alpha: int) -> Color:
    return Color(color.r, color.g, color.b, max(0, min(255, alpha)))


def ease_in_out_sine(progress: float) -> float:
    return -(cos(pi * progress) - 1.0) * 0.5


def ease_out_back(progress: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    shifted = progress - 1.0
    return 1.0 + c3 * shifted * shifted * shifted + c1 * shifted * shifted


def ease_in_back(progress: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    return c3 * progress * progress * progress - c1 * progress * progress


def build_letters(renderer: Renderer2D) -> list[LetterState]:
    total_width = 0.0
    for glyph in WORD:
        total_width += float(renderer.measure_text(glyph, LETTER_SIZE))
    total_width += LETTER_SPACING * float(len(WORD) - 1)

    start_x = (WIDTH - total_width) * 0.5
    center_y = HEIGHT * 0.58
    x = start_x
    letters: list[LetterState] = []

    for index, glyph in enumerate(WORD):
        width = float(renderer.measure_text(glyph, LETTER_SIZE))
        letters.append(
            LetterState(
                glyph=glyph,
                rest_position=Vec2(x + width * 0.5, center_y),
                base_color=PALETTE[index],
            )
        )
        x += width + LETTER_SPACING

    return letters


def reset_letter(letter: LetterState, index: int) -> None:
    direction = -1.0 if index % 2 == 0 else 1.0
    letter.position = Vec2(
        letter.rest_position.x + 140.0 * direction,
        HEIGHT + 110.0 + 16.0 * float(index),
    )
    letter.size = 16
    letter.color = with_alpha(letter.base_color, 0)
    letter.shadow_offset = Vec2(34.0 * direction, 28.0)
    letter.shadow_color = Color(7, 10, 18, 0)


def play_animation(world: World, letters: list[LetterState]) -> None:
    animator = world.get_world_resource(Animator)
    animator.clear()

    for index, letter in enumerate(letters):
        reset_letter(letter, index)

    for index, letter in enumerate(letters):
        direction = -1.0 if index % 2 == 0 else 1.0
        delay = 0.10 * float(index)
        pulse_delay = 0.35 + 0.04 * float(len(letters) - index - 1)

        animator.create().wait(delay).to(
            letter,
            "position",
            Vec2(letter.rest_position.x, letter.rest_position.y - 20.0),
            0.46,
            ease_out_back,
        ).to(
            letter,
            "position",
            letter.rest_position.copy(),
            0.18,
            ease_in_out_sine,
        ).wait(
            pulse_delay,
        ).to(
            letter,
            "position",
            Vec2(letter.rest_position.x, letter.rest_position.y - 16.0),
            0.14,
            ease_in_out_sine,
        ).to(
            letter,
            "position",
            letter.rest_position.copy(),
            0.18,
            ease_in_out_sine,
        ).wait(
            0.90,
        ).to(
            letter,
            "position",
            Vec2(letter.rest_position.x - 36.0 * direction, -120.0),
            0.42,
            ease_in_back,
        ).start()

        animator.create().wait(delay).to(
            letter,
            "size",
            104,
            0.28,
            ease_out_back,
        ).to(
            letter,
            "size",
            LETTER_SIZE,
            0.20,
            ease_in_out_sine,
        ).wait(
            pulse_delay,
        ).to(
            letter,
            "size",
            86,
            0.12,
            ease_in_out_sine,
        ).to(
            letter,
            "size",
            LETTER_SIZE,
            0.16,
            ease_in_out_sine,
        ).wait(
            0.92,
        ).to(
            letter,
            "size",
            18,
            0.30,
            ease_in_back,
        ).start()

        animator.create().wait(delay).to(
            letter,
            "color",
            letter.base_color,
            0.26,
            ease_in_out_sine,
        ).wait(
            0.52,
        ).to(
            letter,
            "color",
            Color(255, 255, 255, 255),
            0.12,
            ease_in_out_sine,
        ).to(
            letter,
            "color",
            letter.base_color,
            0.18,
            ease_in_out_sine,
        ).wait(
            1.02,
        ).to(
            letter,
            "color",
            with_alpha(letter.base_color, 0),
            0.28,
            ease_in_out_sine,
        ).start()

        animator.create().wait(delay).to(
            letter,
            "shadow_offset",
            Vec2(10.0 * direction, 12.0),
            0.30,
            ease_out_back,
        ).to(
            letter,
            "shadow_offset",
            Vec2(8.0, 10.0),
            0.18,
            ease_in_out_sine,
        ).wait(
            pulse_delay + 0.10,
        ).to(
            letter,
            "shadow_offset",
            Vec2(-6.0 * direction, 18.0),
            0.12,
            ease_in_out_sine,
        ).to(
            letter,
            "shadow_offset",
            Vec2(8.0, 10.0),
            0.16,
            ease_in_out_sine,
        ).wait(
            0.88,
        ).to(
            letter,
            "shadow_offset",
            Vec2(30.0 * direction, -12.0),
            0.30,
            ease_in_back,
        ).start()

        animator.create().wait(delay).to(
            letter,
            "shadow_color",
            Color(7, 10, 18, 150),
            0.24,
            ease_in_out_sine,
        ).wait(
            1.64,
        ).to(
            letter,
            "shadow_color",
            Color(7, 10, 18, 0),
            0.26,
            ease_in_out_sine,
        ).start()

    restart_delay = 3.20 + 0.10 * float(len(letters) - 1)
    animator.create().wait(restart_delay).call(
        lambda: play_animation(world, letters)
    ).start()


def draw_letter(renderer: Renderer2D, letter: LetterState) -> None:
    width = float(renderer.measure_text(letter.glyph, letter.size))
    draw_x = letter.position.x - width * 0.5
    draw_y = letter.position.y - float(letter.size) * 0.5

    if letter.shadow_color.a > 0:
        renderer.draw_text(
            letter.glyph,
            (draw_x + letter.shadow_offset.x, draw_y + letter.shadow_offset.y),
            letter.size,
            letter.shadow_color,
        )

    renderer.draw_text(
        letter.glyph,
        (draw_x, draw_y),
        letter.size,
        letter.color,
    )


def render_system(renderer: Renderer2D, letters: list[LetterState]) -> None:
    renderer.start_frame()
    renderer.clear(BACKGROUND)

    renderer.draw_text("Animator: intro, pulse, and exit", (28, 28), 30, TITLE)
    renderer.draw_text(
        "Press SPACE to restart. Each letter combines position, size, color, and shadow.",
        (28, 64),
        18,
        SUBTITLE,
    )

    for letter in letters:
        draw_letter(renderer, letter)

    renderer.draw_text("WORD = AREPY", (28, HEIGHT - 42), 18, SUBTITLE)
    renderer.draw_fps((WIDTH - 96, 16))
    renderer.end_frame()


def main() -> None:
    game = ArepyEngine(
        title="Arepy Animator Letters",
        width=WIDTH,
        height=HEIGHT,
        max_frame_rate=0,
    )
    world = game.create_world("animator_letters")
    letters = build_letters(game.renderer_2d)

    @world.on_startup
    def start() -> None:
        play_animation(world, letters)

    def restart_input(input_device: Input) -> None:
        if input_device.is_key_pressed(Key.SPACE):
            play_animation(world, letters)

    def render_letters(renderer: Renderer2D) -> None:
        render_system(renderer, letters)

    world.add_system(SystemPipeline.UPDATE, restart_input)
    world.add_system(SystemPipeline.RENDER, render_letters)

    game.set_current_world("animator_letters")
    game.run()


if __name__ == "__main__":
    main()
