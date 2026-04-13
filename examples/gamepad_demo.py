from dataclasses import dataclass, field

from arepy import (
    ArepyEngine,
    Color,
    GamepadAxis,
    GamepadButton,
    GamepadDeviceType,
    Input,
    Rect,
    Renderer2D,
    SystemPipeline,
    Time,
)

WIDTH = 1180
HEIGHT = 720
PLAY_LEFT = 24
PLAY_TOP = 24
HUD_WIDTH = 330
PLAY_WIDTH = WIDTH - HUD_WIDTH - 48
PLAY_HEIGHT = HEIGHT - 48
PLAY_RIGHT = PLAY_LEFT + PLAY_WIDTH
PLAY_BOTTOM = PLAY_TOP + PLAY_HEIGHT
PLAYER_RADIUS = 18.0
STICK_DEADZONE = 0.18
BASE_SPEED = 260.0
DPAD_SPEED = 180.0

BACKGROUND = Color(11, 16, 26, 255)
PLAYFIELD = Color(17, 28, 44, 255)
HUD = Color(22, 34, 54, 255)
GRID = Color(42, 62, 88, 255)
TEXT = Color(232, 241, 255, 255)
MUTED = Color(153, 172, 196, 255)
OUTLINE = Color(84, 112, 150, 255)
ACCENTS = [
    Color(255, 113, 91, 255),
    Color(255, 193, 79, 255),
    Color(88, 218, 170, 255),
    Color(88, 151, 255, 255),
]


@dataclass
class DemoState:
    player_x: float = PLAY_LEFT + PLAY_WIDTH * 0.5
    player_y: float = PLAY_TOP + PLAY_HEIGHT * 0.5
    aim_x: float = 1.0
    aim_y: float = 0.0
    accent_index: int = 0
    active_gamepad_id: int | None = None
    connected_ids: tuple[int, ...] = ()
    active_name: str = "No controller detected"
    active_type: GamepadDeviceType = GamepadDeviceType.UNKNOWN
    left_stick: tuple[float, float] = (0.0, 0.0)
    right_stick: tuple[float, float] = (0.0, 0.0)
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    held_buttons: tuple[str, ...] = field(default_factory=tuple)
    vibration_supported: bool = False
    show_help: bool = True


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def apply_deadzone(value: float, deadzone: float = STICK_DEADZONE) -> float:
    magnitude = abs(value)
    if magnitude <= deadzone:
        return 0.0
    scaled = (magnitude - deadzone) / (1.0 - deadzone)
    return scaled if value > 0.0 else -scaled


def normalize_trigger(value: float) -> float:
    return clamp((value + 1.0) * 0.5, 0.0, 1.0)


def cycle_active_gamepad(state: DemoState, direction: int) -> None:
    if not state.connected_ids:
        state.active_gamepad_id = None
        return
    if state.active_gamepad_id not in state.connected_ids:
        state.active_gamepad_id = state.connected_ids[0]
        return

    index = state.connected_ids.index(state.active_gamepad_id)
    next_index = (index + direction) % len(state.connected_ids)
    state.active_gamepad_id = state.connected_ids[next_index]


def collect_held_buttons(input_device: Input, gamepad_id: int) -> tuple[str, ...]:
    labels = (
        (GamepadButton.DPAD_UP, "DPAD_UP"),
        (GamepadButton.DPAD_RIGHT, "DPAD_RIGHT"),
        (GamepadButton.DPAD_DOWN, "DPAD_DOWN"),
        (GamepadButton.DPAD_LEFT, "DPAD_LEFT"),
        (GamepadButton.FACE_UP, "FACE_UP"),
        (GamepadButton.FACE_RIGHT, "FACE_RIGHT"),
        (GamepadButton.FACE_DOWN, "FACE_DOWN"),
        (GamepadButton.FACE_LEFT, "FACE_LEFT"),
        (GamepadButton.LEFT_SHOULDER, "LB"),
        (GamepadButton.RIGHT_SHOULDER, "RB"),
        (GamepadButton.BACK, "BACK"),
        (GamepadButton.START, "START"),
        (GamepadButton.LEFT_STICK, "L3"),
        (GamepadButton.RIGHT_STICK, "R3"),
    )
    return tuple(
        label
        for button, label in labels
        if input_device.is_gamepad_button_down(button, gamepad_id)
    )


def format_device_type(device_type: GamepadDeviceType) -> str:
    return device_type.value.replace("_", " ").title()


def draw_trigger_bar(
    renderer: Renderer2D,
    x: float,
    y: float,
    width: int,
    value: float,
    label: str,
    color: Color,
) -> None:
    fill_width = max(0, min(int(round(width * value)), width))

    renderer.draw_text(label, (x, y - 20), 16, MUTED)
    renderer.draw_rectangle(Rect(x, y, width, 12), PLAYFIELD)
    renderer.draw_rectangle(Rect(x, y, fill_width, 12), color)
    renderer.draw_rectangle_lines_ex(Rect(x, y, width, 12), 2.0, OUTLINE)


def draw_stick_widget(
    renderer: Renderer2D,
    center_x: float,
    center_y: float,
    label: str,
    vector: tuple[float, float],
    color: Color,
) -> None:
    box_size = 86
    half = box_size * 0.5
    renderer.draw_text(label, (center_x - half, center_y - half - 22), 16, MUTED)
    renderer.draw_rectangle(Rect(center_x - half, center_y - half, box_size, box_size), PLAYFIELD)
    renderer.draw_rectangle_lines_ex(
        Rect(center_x - half, center_y - half, box_size, box_size),
        2.0,
        OUTLINE,
    )
    renderer.draw_line_ex((center_x - half, center_y), (center_x + half, center_y), 1.5, GRID)
    renderer.draw_line_ex((center_x, center_y - half), (center_x, center_y + half), 1.5, GRID)
    renderer.draw_circle((center_x + vector[0] * 30.0, center_y + vector[1] * 30.0), 8.0, color)
    renderer.draw_circle_lines((center_x, center_y), 32.0, OUTLINE)


def gamepad_input_system(state: DemoState, input_device: Input, time: Time) -> None:
    state.connected_ids = input_device.get_available_gamepads()

    if not state.connected_ids:
        state.active_gamepad_id = None
        state.active_name = "No controller detected"
        state.active_type = GamepadDeviceType.UNKNOWN
        state.left_stick = (0.0, 0.0)
        state.right_stick = (0.0, 0.0)
        state.left_trigger = 0.0
        state.right_trigger = 0.0
        state.held_buttons = ()
        state.vibration_supported = False
        return

    if state.active_gamepad_id not in state.connected_ids:
        state.active_gamepad_id = state.connected_ids[0]

    gamepad_id = state.active_gamepad_id
    if gamepad_id is None:
        return

    if len(state.connected_ids) > 1:
        if input_device.is_gamepad_button_pressed(GamepadButton.LEFT_SHOULDER, gamepad_id):
            cycle_active_gamepad(state, -1)
        elif input_device.is_gamepad_button_pressed(GamepadButton.RIGHT_SHOULDER, gamepad_id):
            cycle_active_gamepad(state, 1)
        gamepad_id = state.active_gamepad_id or gamepad_id

    state.active_name = input_device.get_gamepad_name(gamepad_id) or "Unknown controller"
    state.active_type = input_device.get_gamepad_device_type(gamepad_id)
    state.vibration_supported = input_device.is_gamepad_vibration_supported(gamepad_id)

    def rumble(left_motor: float, right_motor: float, duration_seconds: float) -> None:
        if state.vibration_supported:
            input_device.set_gamepad_vibration(
                left_motor,
                right_motor,
                duration_seconds,
                gamepad_id,
            )

    left_x = apply_deadzone(
        input_device.get_gamepad_axis_movement(GamepadAxis.LEFT_X, gamepad_id)
    )
    left_y = apply_deadzone(
        input_device.get_gamepad_axis_movement(GamepadAxis.LEFT_Y, gamepad_id)
    )
    right_x = apply_deadzone(
        input_device.get_gamepad_axis_movement(GamepadAxis.RIGHT_X, gamepad_id)
    )
    right_y = apply_deadzone(
        input_device.get_gamepad_axis_movement(GamepadAxis.RIGHT_Y, gamepad_id)
    )

    state.left_trigger = normalize_trigger(
        input_device.get_gamepad_axis_movement(GamepadAxis.LEFT_TRIGGER, gamepad_id)
    )
    state.right_trigger = normalize_trigger(
        input_device.get_gamepad_axis_movement(GamepadAxis.RIGHT_TRIGGER, gamepad_id)
    )
    state.left_stick = (left_x, left_y)
    state.right_stick = (right_x, right_y)

    if input_device.is_gamepad_button_pressed(GamepadButton.BACK, gamepad_id):
        state.show_help = not state.show_help
    if input_device.is_gamepad_button_pressed(GamepadButton.START, gamepad_id):
        state.player_x = PLAY_LEFT + PLAY_WIDTH * 0.5
        state.player_y = PLAY_TOP + PLAY_HEIGHT * 0.5
        rumble(0.2, 0.75, 0.1)

    if input_device.is_gamepad_button_pressed(GamepadButton.FACE_DOWN, gamepad_id):
        state.accent_index = 0
        rumble(0.18, 0.45, 0.08)
    elif input_device.is_gamepad_button_pressed(GamepadButton.FACE_RIGHT, gamepad_id):
        state.accent_index = 1
        rumble(0.18, 0.45, 0.08)
    elif input_device.is_gamepad_button_pressed(GamepadButton.FACE_LEFT, gamepad_id):
        state.accent_index = 2
        rumble(0.18, 0.45, 0.08)
    elif input_device.is_gamepad_button_pressed(GamepadButton.FACE_UP, gamepad_id):
        state.accent_index = 3
        rumble(0.18, 0.45, 0.08)

    if input_device.is_gamepad_button_pressed(GamepadButton.LEFT_STICK, gamepad_id):
        rumble(0.35, 0.85, 0.12)
    elif input_device.is_gamepad_button_pressed(GamepadButton.RIGHT_STICK, gamepad_id):
        rumble(1.0, 1.0, 0.2)

    dpad_x = float(
        input_device.is_gamepad_button_down(GamepadButton.DPAD_RIGHT, gamepad_id)
    ) - float(input_device.is_gamepad_button_down(GamepadButton.DPAD_LEFT, gamepad_id))
    dpad_y = float(
        input_device.is_gamepad_button_down(GamepadButton.DPAD_DOWN, gamepad_id)
    ) - float(input_device.is_gamepad_button_down(GamepadButton.DPAD_UP, gamepad_id))

    precision_scale = 1.0 - state.left_trigger * 0.7
    move_speed = BASE_SPEED + state.right_trigger * 320.0
    move_x = left_x * move_speed + dpad_x * DPAD_SPEED
    move_y = left_y * move_speed + dpad_y * DPAD_SPEED

    state.player_x = clamp(
        state.player_x + move_x * precision_scale * time.delta_seconds,
        PLAY_LEFT + PLAYER_RADIUS,
        PLAY_RIGHT - PLAYER_RADIUS,
    )
    state.player_y = clamp(
        state.player_y + move_y * precision_scale * time.delta_seconds,
        PLAY_TOP + PLAYER_RADIUS,
        PLAY_BOTTOM - PLAYER_RADIUS,
    )

    if right_x != 0.0 or right_y != 0.0:
        length = max((right_x**2 + right_y**2) ** 0.5, 0.001)
        state.aim_x = right_x / length
        state.aim_y = right_y / length

    state.held_buttons = collect_held_buttons(input_device, gamepad_id)


def render_demo(state: DemoState, renderer: Renderer2D) -> None:
    renderer.start_frame()
    renderer.clear(BACKGROUND)

    renderer.draw_rectangle(Rect(PLAY_LEFT, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT), PLAYFIELD)
    renderer.draw_rectangle_lines_ex(
        Rect(PLAY_LEFT, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT), 2.0, OUTLINE
    )
    renderer.draw_rectangle(Rect(PLAY_RIGHT + 18, PLAY_TOP, HUD_WIDTH, PLAY_HEIGHT), HUD)
    renderer.draw_rectangle_lines_ex(
        Rect(PLAY_RIGHT + 18, PLAY_TOP, HUD_WIDTH, PLAY_HEIGHT), 2.0, OUTLINE
    )

    for offset_x in range(64, int(PLAY_WIDTH), 64):
        x = PLAY_LEFT + offset_x
        renderer.draw_line_ex((x, PLAY_TOP), (x, PLAY_BOTTOM), 1.0, GRID)
    for offset_y in range(64, int(PLAY_HEIGHT), 64):
        y = PLAY_TOP + offset_y
        renderer.draw_line_ex((PLAY_LEFT, y), (PLAY_RIGHT, y), 1.0, GRID)

    accent = ACCENTS[state.accent_index]
    pulse_radius = PLAYER_RADIUS + 14.0 + state.right_trigger * 18.0
    player_radius = PLAYER_RADIUS + state.left_trigger * 14.0
    aim_distance = 90.0 + state.right_trigger * 70.0
    aim_end = (
        state.player_x + state.aim_x * aim_distance,
        state.player_y + state.aim_y * aim_distance,
    )

    renderer.draw_circle((state.player_x, state.player_y), player_radius, accent)
    renderer.draw_circle_lines((state.player_x, state.player_y), pulse_radius, OUTLINE)
    renderer.draw_line_ex((state.player_x, state.player_y), aim_end, 3.0, TEXT)
    renderer.draw_circle(aim_end, 7.0, TEXT)
    renderer.draw_circle_lines(aim_end, 15.0, accent)

    renderer.draw_text("Arepy Gamepad Demo", (PLAY_LEFT + 18, PLAY_TOP + 14), 28, TEXT)
    renderer.draw_text(
        "Left stick + dpad move | Right stick aims | Face buttons recolor",
        (PLAY_LEFT + 18, PLAY_TOP + 48),
        18,
        MUTED,
    )

    if state.active_gamepad_id is None:
        renderer.draw_text("No gamepad connected", (PLAY_LEFT + 28, PLAY_TOP + 112), 30, TEXT)
        renderer.draw_text("Connect a controller and move a stick or press a button.", (PLAY_LEFT + 28, PLAY_TOP + 152), 20, MUTED)
        renderer.draw_text("Xbox pads usually work by USB or Bluetooth.", (PLAY_LEFT + 28, PLAY_TOP + 192), 18, MUTED)
        renderer.draw_text("For DualSense/DualShock on Windows, USB is the safest first test.", (PLAY_LEFT + 28, PLAY_TOP + 220), 18, MUTED)
        renderer.draw_text("This demo uses raylib directly, with no SDL layer in between.", (PLAY_LEFT + 28, PLAY_TOP + 248), 18, MUTED)
    else:
        renderer.draw_text(
            f"Active pad: {state.active_gamepad_id}",
            (PLAY_RIGHT + 38, PLAY_TOP + 18),
            22,
            TEXT,
        )
        renderer.draw_text(
            f"Type: {format_device_type(state.active_type)}",
            (PLAY_RIGHT + 38, PLAY_TOP + 52),
            18,
            MUTED,
        )
        renderer.draw_text(
            state.active_name,
            (PLAY_RIGHT + 38, PLAY_TOP + 78),
            18,
            TEXT,
        )

        connected_label = ", ".join(str(gamepad_id) for gamepad_id in state.connected_ids)
        renderer.draw_text(
            f"Connected slots: {connected_label}",
            (PLAY_RIGHT + 38, PLAY_TOP + 110),
            16,
            MUTED,
        )
        renderer.draw_text(
            "Rumble: available" if state.vibration_supported else "Rumble: unavailable on this backend",
            (PLAY_RIGHT + 38, PLAY_TOP + 132),
            16,
            MUTED,
        )

        draw_trigger_bar(
            renderer,
            PLAY_RIGHT + 38,
            PLAY_TOP + 166,
            252,
            state.left_trigger,
            "LT precision",
            ACCENTS[2],
        )
        draw_trigger_bar(
            renderer,
            PLAY_RIGHT + 38,
            PLAY_TOP + 216,
            252,
            state.right_trigger,
            "RT boost",
            ACCENTS[1],
        )
        draw_stick_widget(
            renderer,
            PLAY_RIGHT + 104,
            PLAY_TOP + 342,
            "Left stick",
            state.left_stick,
            ACCENTS[0],
        )
        draw_stick_widget(
            renderer,
            PLAY_RIGHT + 242,
            PLAY_TOP + 342,
            "Right stick",
            state.right_stick,
            ACCENTS[3],
        )

        buttons_text = ", ".join(state.held_buttons) if state.held_buttons else "none"
        renderer.draw_text("Held buttons", (PLAY_RIGHT + 38, PLAY_TOP + 418), 18, TEXT)
        renderer.draw_text(buttons_text, (PLAY_RIGHT + 38, PLAY_TOP + 444), 16, MUTED)

        if state.show_help:
            help_lines = [
                "FACE_DOWN / RIGHT / LEFT / UP: switch color",
                "START: center the player",
                (
                    "L3: short rumble | R3: strong rumble"
                    if state.vibration_supported
                    else "Rumble is unavailable on this raylib build"
                ),
                "BACK: hide this help",
                "LB / RB: switch active pad when multiple are connected",
            ]
            y = PLAY_TOP + 496
            for line in help_lines:
                renderer.draw_text(line, (PLAY_RIGHT + 38, y), 16, MUTED)
                y += 24
        else:
            renderer.draw_text(
                "Press BACK to show help again",
                (PLAY_RIGHT + 38, PLAY_TOP + 496),
                16,
                MUTED,
            )

    renderer.draw_fps((PLAY_RIGHT + 38, PLAY_BOTTOM - 30))
    renderer.end_frame()


def main() -> None:
    state = DemoState()
    engine = ArepyEngine(
        title="Arepy Gamepad Demo",
        width=WIDTH,
        height=HEIGHT,
        max_frame_rate=0,
    )
    world = engine.create_world("gamepad_demo")

    def input_system(input_device: Input, time: Time) -> None:
        gamepad_input_system(state, input_device, time)

    def render_system(renderer: Renderer2D) -> None:
        render_demo(state, renderer)

    world.add_system(SystemPipeline.INPUT, input_system)
    world.add_system(SystemPipeline.RENDER, render_system)

    engine.set_current_world("gamepad_demo")
    engine.run()


if __name__ == "__main__":
    main()