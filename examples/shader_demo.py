"""Minimal shader demo: speech bubble with a unified pixel-art tail."""

from math import atan2, pi

from arepy import (
    ArepyEngine,
    ArepyShader,
    Color,
    Input,
    Rect,
    Renderer2D,
    ShaderUniformType,
    SystemPipeline,
    WindowFlag,
)
from arepy.ecs.world import World

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640

PIXEL_SIZE = 8
FONT_SIZE = 22
LINE_GAP = 8
PADDING_X = 40
PADDING_Y = 32
MAX_TEXT_WIDTH = 320
MIN_BUBBLE_WIDTH = 192
MIN_BUBBLE_HEIGHT = 112
TAIL_HEIGHT = 32
OUTER_RADIUS_CELLS = 6
WORD_DELAY = 0.12
MESSAGE_HOLD = 1.35
NO_TAIL_MODE = -1

BACKGROUND = Color(239, 230, 214, 255)
TEXT_COLOR = Color(24, 20, 18, 255)
WHITE = Color(255, 255, 255, 255)
FILL_UNIFORM = Color(255, 252, 244, 255).normalize()
OUTLINE_UNIFORM = Color(18, 16, 15, 255).normalize()

MESSAGES = [
    "Heroe, te hemos estado esperando.",
    "Necesitamos tu ayuda para salvar el reino de las garras del malvado rey demonio.",
    "Solo tú puedes derrotarlo y restaurar la paz en el reino.",
]

FRAGMENT_SHADER = """
#version 330

in vec4 fragColor;
out vec4 finalColor;

uniform vec2 u_origin;
uniform float u_screen_height;
uniform vec2 u_body_size;
uniform float u_tail_height;
uniform float u_pixel_size;
uniform vec2 u_tail_anchor;
uniform int u_tail_mode;
uniform vec4 u_fill_color;
uniform vec4 u_outline_color;

const int OUTER_RADIUS = 6;

int procedural_trim(int row, int radius) {
    float float_radius = float(radius);
    float y = float_radius - float(row) - 0.5;
    float x = float_radius - sqrt(max(0.0, float_radius * float_radius - y * y));
    return int(ceil(x));
}

int outer_trim(int row, int radius) {
    if (radius == 6) {
        if (row == 0) return 5;
        if (row == 1) return 4;
        if (row == 2) return 3;
        if (row == 3) return 2;
        if (row == 4) return 1;
        return 0;
    }

    if (radius == 5) {
        if (row == 0) return 4;
        if (row == 1) return 3;
        if (row == 2) return 2;
        if (row == 3) return 1;
        return 0;
    }

    return procedural_trim(row, radius);
}

int body_radius(ivec2 size) {
    return min(OUTER_RADIUS, max(1, min(size.x, size.y) / 2 - 1));
}

bool in_body(ivec2 cell, ivec2 size) {
    if (cell.x < 0 || cell.y < 0 || cell.x >= size.x || cell.y >= size.y) {
        return false;
    }

    int radius = body_radius(size);
    int right = size.x - 1 - cell.x;
    int bottom = size.y - 1 - cell.y;

    if (cell.x < radius && cell.y < radius) {
        return cell.x >= outer_trim(cell.y, radius);
    }
    if (right < radius && cell.y < radius) {
        return right >= outer_trim(cell.y, radius);
    }
    if (cell.x < radius && bottom < radius) {
        return cell.x >= outer_trim(bottom, radius);
    }
    if (right < radius && bottom < radius) {
        return right >= outer_trim(bottom, radius);
    }

    return true;
}

ivec2 tail_relative_cell(ivec2 cell) {
    vec2 cell_center = vec2(cell) + vec2(0.5, 0.5);
    vec2 anchor_center = u_tail_anchor / u_pixel_size;
    return ivec2(round(cell_center - anchor_center));
}

bool in_straight_tail_base(ivec2 rel) {
    int depth = rel.x;
    int offset = abs(rel.y);

    if (depth < 0 || depth > 4) {
        return false;
    }
    if (depth <= 1) {
        return offset <= 3;
    }
    if (depth == 2) {
        return offset <= 2;
    }
    if (depth == 3) {
        return offset <= 1;
    }

    return offset == 0;
}

bool in_diagonal_tail_base(ivec2 rel) {
    if (rel.x < 0 || rel.y < 0 || rel.x > 7 || rel.y > 7) {
        return false;
    }

    int diff = abs(rel.x - rel.y);
    int sum = rel.x + rel.y;
    return diff <= 2 && sum >= 3 && sum <= 11;
}

bool in_tail(ivec2 cell) {
    if (u_tail_mode < 0) {
        return false;
    }

    ivec2 rel = tail_relative_cell(cell);

    if (u_tail_mode == 0) {
        return in_straight_tail_base(rel);
    }
    if (u_tail_mode == 1) {
        return in_diagonal_tail_base(rel);
    }
    if (u_tail_mode == 2) {
        return in_straight_tail_base(ivec2(rel.y, rel.x));
    }
    if (u_tail_mode == 3) {
        return in_diagonal_tail_base(ivec2(-rel.x, rel.y));
    }
    if (u_tail_mode == 4) {
        return in_straight_tail_base(ivec2(-rel.x, rel.y));
    }
    if (u_tail_mode == 5) {
        return in_diagonal_tail_base(ivec2(-rel.x, -rel.y));
    }
    if (u_tail_mode == 6) {
        return in_straight_tail_base(ivec2(-rel.y, rel.x));
    }

    return in_diagonal_tail_base(ivec2(rel.x, -rel.y));
}

bool occupied_cell(ivec2 cell, ivec2 body_origin, ivec2 body_cells) {
    return in_body(cell - body_origin, body_cells) || in_tail(cell);
}

void main() {
    vec2 local = vec2(
        gl_FragCoord.x - u_origin.x,
        (u_screen_height - gl_FragCoord.y) - u_origin.y
    );

    ivec2 cell = ivec2(floor(local / u_pixel_size));
    int margin = max(1, int(round(u_tail_height / u_pixel_size)));
    ivec2 body_origin = ivec2(margin, margin);
    ivec2 body_cells = ivec2(max(vec2(1.0), floor(u_body_size / u_pixel_size)));

    if (!occupied_cell(cell, body_origin, body_cells)) {
        discard;
    }

    bool outline =
        !occupied_cell(cell + ivec2(1, 0), body_origin, body_cells)
        || !occupied_cell(cell + ivec2(-1, 0), body_origin, body_cells)
        || !occupied_cell(cell + ivec2(0, 1), body_origin, body_cells)
        || !occupied_cell(cell + ivec2(0, -1), body_origin, body_cells);

    finalColor = (outline ? u_outline_color : u_fill_color) * fragColor;
}
"""


def snap_to_grid(value: float) -> int:
    return max(PIXEL_SIZE, int(round(value / PIXEL_SIZE)) * PIXEL_SIZE)


def snap_cell_center(value: float) -> float:
    return (
        int(round((value - PIXEL_SIZE * 0.5) / PIXEL_SIZE)) * PIXEL_SIZE
        + PIXEL_SIZE * 0.5
    )


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def outer_radius_cells(body_width: int, body_height: int) -> int:
    width_cells = max(1, body_width // PIXEL_SIZE)
    height_cells = max(1, body_height // PIXEL_SIZE)
    return min(OUTER_RADIUS_CELLS, max(1, min(width_cells, height_cells) // 2 - 1))


def wrap_text(
    renderer: Renderer2D,
    text: str,
    font_size: int,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines = [words[0]]
    for word in words[1:]:
        candidate = f"{lines[-1]} {word}"
        if renderer.measure_text(candidate, font_size) <= max_width:
            lines[-1] = candidate
        else:
            lines.append(word)

    return lines


def tail_mode_from_mouse(
    mouse_position: tuple[float, float],
    bubble_center: tuple[float, float],
) -> int:
    dx = mouse_position[0] - bubble_center[0]
    dy = mouse_position[1] - bubble_center[1]
    angle = atan2(dy, dx)
    sector = int(((angle + pi / 8.0) % (2.0 * pi)) / (pi / 4.0))
    if sector in (0, 4):
        return NO_TAIL_MODE
    return sector


def compute_tail_anchor(
    mode: int,
    mouse_position: tuple[float, float],
    body_x: int,
    body_y: int,
    body_width: int,
    body_height: int,
) -> tuple[float, float]:
    center_x = body_x + body_width * 0.5
    center_y = body_y + body_height * 0.5
    if mode == NO_TAIL_MODE:
        return center_x, center_y

    dx = mouse_position[0] - center_x
    dy = mouse_position[1] - center_y
    if abs(dx) <= 1e-6 and abs(dy) <= 1e-6:
        dx = 1.0

    half_width = max(PIXEL_SIZE * 0.5, body_width * 0.5 - PIXEL_SIZE * 0.5)
    half_height = max(PIXEL_SIZE * 0.5, body_height * 0.5 - PIXEL_SIZE * 0.5)
    tx = float("inf") if abs(dx) <= 1e-6 else half_width / abs(dx)
    ty = float("inf") if abs(dy) <= 1e-6 else half_height / abs(dy)

    right_x = body_x + body_width - PIXEL_SIZE * 0.5
    left_x = body_x + PIXEL_SIZE * 0.5
    bottom_y = body_y + body_height - PIXEL_SIZE * 0.5
    top_y = body_y + PIXEL_SIZE * 0.5

    corner_offset = max(0, outer_radius_cells(body_width, body_height) - 1) * PIXEL_SIZE
    corner_right_x = right_x - corner_offset
    corner_left_x = left_x + corner_offset
    corner_bottom_y = bottom_y - corner_offset
    corner_top_y = top_y + corner_offset

    if mode == 0:
        return right_x, snap_cell_center(
            clamp(center_y + dy * tx, corner_top_y, corner_bottom_y)
        )
    if mode == 1:
        return corner_right_x, corner_bottom_y
    if mode == 2:
        return (
            snap_cell_center(clamp(center_x + dx * ty, corner_left_x, corner_right_x)),
            bottom_y,
        )
    if mode == 3:
        return corner_left_x, corner_bottom_y
    if mode == 4:
        return left_x, snap_cell_center(
            clamp(center_y + dy * tx, corner_top_y, corner_bottom_y)
        )
    if mode == 5:
        return corner_left_x, corner_top_y
    if mode == 6:
        return (
            snap_cell_center(clamp(center_x + dx * ty, corner_left_x, corner_right_x)),
            top_y,
        )
    return corner_right_x, corner_top_y


def draw_bubble(
    renderer: Renderer2D,
    shader: ArepyShader,
    x: int,
    y: int,
    body_width: int,
    body_height: int,
    tail_anchor: tuple[float, float],
    tail_mode: int,
) -> None:
    renderer.set_shader_value(
        shader,
        ShaderUniformType.VEC2,
        "u_origin",
        (float(x), float(y)),
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.FLOAT,
        "u_screen_height",
        float(WINDOW_HEIGHT),
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.VEC2,
        "u_body_size",
        (float(body_width), float(body_height)),
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.FLOAT,
        "u_tail_height",
        float(TAIL_HEIGHT),
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.FLOAT,
        "u_pixel_size",
        float(PIXEL_SIZE),
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.VEC2,
        "u_tail_anchor",
        (float(tail_anchor[0] - x), float(tail_anchor[1] - y)),
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.INT,
        "u_tail_mode",
        tail_mode,
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.VEC4,
        "u_fill_color",
        FILL_UNIFORM,
    )
    renderer.set_shader_value(
        shader,
        ShaderUniformType.VEC4,
        "u_outline_color",
        OUTLINE_UNIFORM,
    )

    outer_width = body_width + TAIL_HEIGHT * 2
    outer_height = body_height + TAIL_HEIGHT * 2

    renderer.begin_shader_mode(shader)
    renderer.draw_rectangle(Rect(x, y, outer_width, outer_height), WHITE)
    renderer.end_shader_mode()


def build_render_system(shader: ArepyShader):
    message_index = 0
    reveal_timer = 0.0
    hold_timer = 0.0
    visible_word_count = 1

    def render_system(renderer: Renderer2D, input_device: Input) -> None:
        nonlocal hold_timer
        nonlocal message_index
        nonlocal reveal_timer
        nonlocal visible_word_count

        delta_time = renderer.get_delta_time()
        words = MESSAGES[message_index].split()

        if visible_word_count < len(words):
            reveal_timer += delta_time
            while reveal_timer >= WORD_DELAY and visible_word_count < len(words):
                reveal_timer -= WORD_DELAY
                visible_word_count += 1
        else:
            hold_timer += delta_time
            if hold_timer >= MESSAGE_HOLD:
                message_index = (message_index + 1) % len(MESSAGES)
                visible_word_count = 1
                reveal_timer = 0.0
                hold_timer = 0.0
                words = MESSAGES[message_index].split()

        visible_text = " ".join(words[:visible_word_count])
        lines = wrap_text(renderer, visible_text, FONT_SIZE, MAX_TEXT_WIDTH)
        line_widths = [renderer.measure_text(line, FONT_SIZE) for line in lines]
        text_width = max(line_widths, default=0)
        text_height = len(lines) * FONT_SIZE + max(0, len(lines) - 1) * LINE_GAP
        body_width = snap_to_grid(max(MIN_BUBBLE_WIDTH, text_width + PADDING_X * 2))
        body_height = snap_to_grid(max(MIN_BUBBLE_HEIGHT, text_height + PADDING_Y * 2))
        outer_width = body_width + TAIL_HEIGHT * 2
        outer_height = body_height + TAIL_HEIGHT * 2
        bubble_x = snap_to_grid((WINDOW_WIDTH - outer_width) * 0.5)
        bubble_y = snap_to_grid((WINDOW_HEIGHT - outer_height) * 0.5)
        body_x = bubble_x + TAIL_HEIGHT
        body_y = bubble_y + TAIL_HEIGHT
        mouse_position = input_device.get_mouse_position()
        bubble_center = (bubble_x + outer_width * 0.5, bubble_y + outer_height * 0.5)
        tail_mode = tail_mode_from_mouse(mouse_position, bubble_center)
        tail_anchor = compute_tail_anchor(
            tail_mode,
            mouse_position,
            body_x,
            body_y,
            body_width,
            body_height,
        )

        renderer.start_frame()
        renderer.clear(BACKGROUND)

        draw_bubble(
            renderer,
            shader,
            bubble_x,
            bubble_y,
            body_width,
            body_height,
            tail_anchor,
            tail_mode,
        )

        text_x = body_x + PADDING_X
        text_y = body_y + PADDING_Y
        for index, line in enumerate(lines):
            line_y = text_y + index * (FONT_SIZE + LINE_GAP)
            renderer.draw_text(line, (text_x, line_y), FONT_SIZE, TEXT_COLOR)

        renderer.end_frame()

    return render_system


def main() -> None:
    engine = ArepyEngine(
        title="Speech Bubble Shader Demo",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        max_frame_rate=60,
        window_flags=WindowFlag.VSYNC_HINT,
    )

    renderer = engine.get_resource(Renderer2D)
    shader = renderer.compile_shader(fragment_source=FRAGMENT_SHADER)

    world: World = engine.create_world("main")
    world.add_system(SystemPipeline.RENDER, build_render_system(shader))

    @world.on_shutdown
    def cleanup_shader() -> None:
        renderer.unload_shader(shader)

    engine.set_current_world("main")
    engine.run()


if __name__ == "__main__":
    main()
