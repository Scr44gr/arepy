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

GAMEPAD_BUTTON_LABELS = (
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

PLAYFIELD_RECT = Rect(PLAY_LEFT, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT)
HUD_RECT = Rect(PLAY_RIGHT + 18, PLAY_TOP, HUD_WIDTH, PLAY_HEIGHT)
GRID_LINES = tuple(
    ((PLAY_LEFT + offset, PLAY_TOP), (PLAY_LEFT + offset, PLAY_BOTTOM))
    for offset in range(64, int(PLAY_WIDTH), 64)
) + tuple(
    ((PLAY_LEFT, PLAY_TOP + offset), (PLAY_RIGHT, PLAY_TOP + offset))
    for offset in range(64, int(PLAY_HEIGHT), 64)
)

TITLE_POSITION = (PLAY_LEFT + 18, PLAY_TOP + 14)
SUBTITLE_POSITION = (PLAY_LEFT + 18, PLAY_TOP + 48)
NO_GAMEPAD_TITLE_POSITION = (PLAY_LEFT + 28, PLAY_TOP + 112)
NO_GAMEPAD_HINT_POSITION = (PLAY_LEFT + 28, PLAY_TOP + 152)
NO_GAMEPAD_XBOX_POSITION = (PLAY_LEFT + 28, PLAY_TOP + 192)
NO_GAMEPAD_PLAYSTATION_POSITION = (PLAY_LEFT + 28, PLAY_TOP + 220)
NO_GAMEPAD_BACKEND_POSITION = (PLAY_LEFT + 28, PLAY_TOP + 248)

HUD_LEFT = PLAY_RIGHT + 38
ACTIVE_PAD_POSITION = (HUD_LEFT, PLAY_TOP + 18)
DEVICE_TYPE_POSITION = (HUD_LEFT, PLAY_TOP + 52)
DEVICE_NAME_POSITION = (HUD_LEFT, PLAY_TOP + 78)
CONNECTED_SLOTS_POSITION = (HUD_LEFT, PLAY_TOP + 110)
RUMBLE_STATUS_POSITION = (HUD_LEFT, PLAY_TOP + 132)
HELD_BUTTONS_TITLE_POSITION = (HUD_LEFT, PLAY_TOP + 418)
HELD_BUTTONS_POSITION = (HUD_LEFT, PLAY_TOP + 444)
HELP_HIDDEN_POSITION = (HUD_LEFT, PLAY_TOP + 496)
FPS_POSITION = (HUD_LEFT, PLAY_BOTTOM - 30)

HELP_LINES_WITH_RUMBLE = (
    "FACE_DOWN / RIGHT / LEFT / UP: switch color",
    "START: center the player",
    "L3: short rumble | R3: strong rumble",
    "BACK: hide this help",
    "LB / RB: switch active pad when multiple are connected",
)
HELP_LINES_WITHOUT_RUMBLE = (
    "FACE_DOWN / RIGHT / LEFT / UP: switch color",
    "START: center the player",
    "Rumble is unavailable on this raylib build",
    "BACK: hide this help",
    "LB / RB: switch active pad when multiple are connected",
)
HELP_LINE_POSITIONS = tuple(
    (HUD_LEFT, PLAY_TOP + 496 + index * 24)
    for index in range(len(HELP_LINES_WITH_RUMBLE))
)
HELP_ROWS_WITH_RUMBLE = tuple(zip(HELP_LINES_WITH_RUMBLE, HELP_LINE_POSITIONS))
HELP_ROWS_WITHOUT_RUMBLE = tuple(zip(HELP_LINES_WITHOUT_RUMBLE, HELP_LINE_POSITIONS))


@dataclass(slots=True)
class TriggerBarGeometry:
    label_position: tuple[float, float]
    track: Rect
    fill: Rect


@dataclass(slots=True)
class StickWidgetGeometry:
    label_position: tuple[float, float]
    box: Rect
    horizontal_start: tuple[float, float]
    horizontal_end: tuple[float, float]
    vertical_start: tuple[float, float]
    vertical_end: tuple[float, float]
    center: tuple[float, float]
    cursor: list[float]


def make_trigger_bar_geometry(x: float, y: float, width: int) -> TriggerBarGeometry:
    return TriggerBarGeometry(
        label_position=(x, y - 20),
        track=Rect(x, y, width, 12),
        fill=Rect(x, y, 0, 12),
    )


def make_stick_widget_geometry(
    center_x: float,
    center_y: float,
) -> StickWidgetGeometry:
    box_size = 86
    half = box_size * 0.5
    return StickWidgetGeometry(
        label_position=(center_x - half, center_y - half - 22),
        box=Rect(center_x - half, center_y - half, box_size, box_size),
        horizontal_start=(center_x - half, center_y),
        horizontal_end=(center_x + half, center_y),
        vertical_start=(center_x, center_y - half),
        vertical_end=(center_x, center_y + half),
        center=(center_x, center_y),
        cursor=[center_x, center_y],
    )


@dataclass(slots=True)
class DemoState:
    player_x: float = PLAY_LEFT + PLAY_WIDTH * 0.5
    player_y: float = PLAY_TOP + PLAY_HEIGHT * 0.5
    aim_x: float = 1.0
    aim_y: float = 0.0
    accent_index: int = 0
    active_gamepad_id: int | None = None
    connected_ids: tuple[int, ...] = ()
    connected_label: str = ""
    active_name: str = "No controller detected"
    active_type: GamepadDeviceType = GamepadDeviceType.UNKNOWN
    active_type_label: str = "Unknown"
    left_stick: list[float] = field(default_factory=lambda: [0.0, 0.0])
    right_stick: list[float] = field(default_factory=lambda: [0.0, 0.0])
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    held_buttons: list[str] = field(default_factory=list)
    held_buttons_label: str = "none"
    vibration_supported: bool = False
    show_help: bool = True
    player_position: list[float] = field(
        default_factory=lambda: [
            PLAY_LEFT + PLAY_WIDTH * 0.5,
            PLAY_TOP + PLAY_HEIGHT * 0.5,
        ],
        init=False,
        repr=False,
    )
    aim_end: list[float] = field(
        default_factory=lambda: [0.0, 0.0],
        init=False,
        repr=False,
    )
    left_trigger_geometry: TriggerBarGeometry = field(
        default_factory=lambda: make_trigger_bar_geometry(
            HUD_LEFT,
            PLAY_TOP + 166,
            252,
        ),
        init=False,
        repr=False,
    )
    right_trigger_geometry: TriggerBarGeometry = field(
        default_factory=lambda: make_trigger_bar_geometry(
            HUD_LEFT,
            PLAY_TOP + 216,
            252,
        ),
        init=False,
        repr=False,
    )
    left_stick_geometry: StickWidgetGeometry = field(
        default_factory=lambda: make_stick_widget_geometry(
            PLAY_RIGHT + 104,
            PLAY_TOP + 342,
        ),
        init=False,
        repr=False,
    )
    right_stick_geometry: StickWidgetGeometry = field(
        default_factory=lambda: make_stick_widget_geometry(
            PLAY_RIGHT + 242,
            PLAY_TOP + 342,
        ),
        init=False,
        repr=False,
    )
    held_buttons_scratch: list[str] = field(
        default_factory=list,
        init=False,
        repr=False,
    )


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


def collect_held_buttons(
    state: DemoState,
    input_device: Input,
    gamepad_id: int,
) -> None:
    held_buttons = state.held_buttons_scratch
    held_buttons.clear()
    for button, label in GAMEPAD_BUTTON_LABELS:
        if input_device.is_gamepad_button_down(button, gamepad_id):
            held_buttons.append(label)

    if held_buttons == state.held_buttons:
        return

    state.held_buttons, state.held_buttons_scratch = (
        held_buttons,
        state.held_buttons,
    )
    state.held_buttons_label = ", ".join(held_buttons) if held_buttons else "none"


def format_device_type(device_type: GamepadDeviceType) -> str:
    return device_type.value.replace("_", " ").title()


def draw_trigger_bar(
    renderer: Renderer2D,
    geometry: TriggerBarGeometry,
    value: float,
    label: str,
    color: Color,
) -> None:
    track = geometry.track
    geometry.fill.width = max(
        0,
        min(int(round(track.width * value)), track.width),
    )

    renderer.draw_text(label, geometry.label_position, 16, MUTED)
    renderer.draw_rectangle(track, PLAYFIELD)
    renderer.draw_rectangle(geometry.fill, color)
    renderer.draw_rectangle_lines_ex(track, 2.0, OUTLINE)


def draw_stick_widget(
    renderer: Renderer2D,
    geometry: StickWidgetGeometry,
    label: str,
    vector: list[float],
    color: Color,
) -> None:
    center = geometry.center
    cursor = geometry.cursor
    cursor[0] = center[0] + vector[0] * 30.0
    cursor[1] = center[1] + vector[1] * 30.0

    renderer.draw_text(label, geometry.label_position, 16, MUTED)
    renderer.draw_rectangle(geometry.box, PLAYFIELD)
    renderer.draw_rectangle_lines_ex(geometry.box, 2.0, OUTLINE)
    renderer.draw_line_ex(
        geometry.horizontal_start,
        geometry.horizontal_end,
        1.5,
        GRID,
    )
    renderer.draw_line_ex(
        geometry.vertical_start,
        geometry.vertical_end,
        1.5,
        GRID,
    )
    renderer.draw_circle(cursor, 8.0, color)
    renderer.draw_circle_lines(center, 32.0, OUTLINE)


def rumble(
    input_device: Input,
    state: DemoState,
    gamepad_id: int,
    left_motor: float,
    right_motor: float,
    duration_seconds: float,
) -> None:
    if state.vibration_supported:
        input_device.set_gamepad_vibration(
            left_motor,
            right_motor,
            duration_seconds,
            gamepad_id,
        )


def gamepad_input_system(state: DemoState, input_device: Input, time: Time) -> None:
    connected_ids = input_device.get_available_gamepads()
    if connected_ids != state.connected_ids:
        state.connected_ids = connected_ids
        state.connected_label = ", ".join(
            str(gamepad_id) for gamepad_id in connected_ids
        )

    if not state.connected_ids:
        state.active_gamepad_id = None
        state.active_name = "No controller detected"
        state.active_type = GamepadDeviceType.UNKNOWN
        state.active_type_label = "Unknown"
        state.left_stick[0] = 0.0
        state.left_stick[1] = 0.0
        state.right_stick[0] = 0.0
        state.right_stick[1] = 0.0
        state.left_trigger = 0.0
        state.right_trigger = 0.0
        state.held_buttons.clear()
        state.held_buttons_scratch.clear()
        state.held_buttons_label = "none"
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
    active_type = input_device.get_gamepad_device_type(gamepad_id)
    if active_type is not state.active_type:
        state.active_type = active_type
        state.active_type_label = format_device_type(active_type)
    state.vibration_supported = input_device.is_gamepad_vibration_supported(gamepad_id)

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
    state.left_stick[0] = left_x
    state.left_stick[1] = left_y
    state.right_stick[0] = right_x
    state.right_stick[1] = right_y

    if input_device.is_gamepad_button_pressed(GamepadButton.BACK, gamepad_id):
        state.show_help = not state.show_help
    if input_device.is_gamepad_button_pressed(GamepadButton.START, gamepad_id):
        state.player_x = PLAY_LEFT + PLAY_WIDTH * 0.5
        state.player_y = PLAY_TOP + PLAY_HEIGHT * 0.5
        rumble(input_device, state, gamepad_id, 0.2, 0.75, 0.1)

    if input_device.is_gamepad_button_pressed(GamepadButton.FACE_DOWN, gamepad_id):
        state.accent_index = 0
        rumble(input_device, state, gamepad_id, 0.18, 0.45, 0.08)
    elif input_device.is_gamepad_button_pressed(GamepadButton.FACE_RIGHT, gamepad_id):
        state.accent_index = 1
        rumble(input_device, state, gamepad_id, 0.18, 0.45, 0.08)
    elif input_device.is_gamepad_button_pressed(GamepadButton.FACE_LEFT, gamepad_id):
        state.accent_index = 2
        rumble(input_device, state, gamepad_id, 0.18, 0.45, 0.08)
    elif input_device.is_gamepad_button_pressed(GamepadButton.FACE_UP, gamepad_id):
        state.accent_index = 3
        rumble(input_device, state, gamepad_id, 0.18, 0.45, 0.08)

    if input_device.is_gamepad_button_pressed(GamepadButton.LEFT_STICK, gamepad_id):
        rumble(input_device, state, gamepad_id, 0.35, 0.85, 0.12)
    elif input_device.is_gamepad_button_pressed(GamepadButton.RIGHT_STICK, gamepad_id):
        rumble(input_device, state, gamepad_id, 1.0, 1.0, 0.2)

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

    collect_held_buttons(state, input_device, gamepad_id)


def render_demo(state: DemoState, renderer: Renderer2D) -> None:
    renderer.start_frame()
    renderer.clear(BACKGROUND)

    renderer.draw_rectangle(PLAYFIELD_RECT, PLAYFIELD)
    renderer.draw_rectangle_lines_ex(PLAYFIELD_RECT, 2.0, OUTLINE)
    renderer.draw_rectangle(HUD_RECT, HUD)
    renderer.draw_rectangle_lines_ex(HUD_RECT, 2.0, OUTLINE)

    for start, end in GRID_LINES:
        renderer.draw_line_ex(start, end, 1.0, GRID)

    accent = ACCENTS[state.accent_index]
    pulse_radius = PLAYER_RADIUS + 14.0 + state.right_trigger * 18.0
    player_radius = PLAYER_RADIUS + state.left_trigger * 14.0
    aim_distance = 90.0 + state.right_trigger * 70.0
    player_position = state.player_position
    player_position[0] = state.player_x
    player_position[1] = state.player_y
    aim_end = state.aim_end
    aim_end[0] = state.player_x + state.aim_x * aim_distance
    aim_end[1] = state.player_y + state.aim_y * aim_distance

    renderer.draw_circle(player_position, player_radius, accent)
    renderer.draw_circle_lines(player_position, pulse_radius, OUTLINE)
    renderer.draw_line_ex(player_position, aim_end, 3.0, TEXT)
    renderer.draw_circle(aim_end, 7.0, TEXT)
    renderer.draw_circle_lines(aim_end, 15.0, accent)

    renderer.draw_text("Arepy Gamepad Demo", TITLE_POSITION, 28, TEXT)
    renderer.draw_text(
        "Left stick + dpad move | Right stick aims | Face buttons recolor",
        SUBTITLE_POSITION,
        18,
        MUTED,
    )

    if state.active_gamepad_id is None:
        renderer.draw_text("No gamepad connected", NO_GAMEPAD_TITLE_POSITION, 30, TEXT)
        renderer.draw_text(
            "Connect a controller and move a stick or press a button.",
            NO_GAMEPAD_HINT_POSITION,
            20,
            MUTED,
        )
        renderer.draw_text(
            "Xbox pads usually work by USB or Bluetooth.",
            NO_GAMEPAD_XBOX_POSITION,
            18,
            MUTED,
        )
        renderer.draw_text(
            "For DualSense/DualShock on Windows, USB is the safest first test.",
            NO_GAMEPAD_PLAYSTATION_POSITION,
            18,
            MUTED,
        )
        renderer.draw_text(
            "This demo uses raylib directly, with no SDL layer in between.",
            NO_GAMEPAD_BACKEND_POSITION,
            18,
            MUTED,
        )
    else:
        renderer.draw_text(
            f"Active pad: {state.active_gamepad_id}",
            ACTIVE_PAD_POSITION,
            22,
            TEXT,
        )
        renderer.draw_text(
            f"Type: {state.active_type_label}",
            DEVICE_TYPE_POSITION,
            18,
            MUTED,
        )
        renderer.draw_text(
            state.active_name,
            DEVICE_NAME_POSITION,
            18,
            TEXT,
        )

        renderer.draw_text(
            f"Connected slots: {state.connected_label}",
            CONNECTED_SLOTS_POSITION,
            16,
            MUTED,
        )
        renderer.draw_text(
            (
                "Rumble: available"
                if state.vibration_supported
                else "Rumble: unavailable on this backend"
            ),
            RUMBLE_STATUS_POSITION,
            16,
            MUTED,
        )

        draw_trigger_bar(
            renderer,
            state.left_trigger_geometry,
            state.left_trigger,
            "LT precision",
            ACCENTS[2],
        )
        draw_trigger_bar(
            renderer,
            state.right_trigger_geometry,
            state.right_trigger,
            "RT boost",
            ACCENTS[1],
        )
        draw_stick_widget(
            renderer,
            state.left_stick_geometry,
            "Left stick",
            state.left_stick,
            ACCENTS[0],
        )
        draw_stick_widget(
            renderer,
            state.right_stick_geometry,
            "Right stick",
            state.right_stick,
            ACCENTS[3],
        )

        renderer.draw_text("Held buttons", HELD_BUTTONS_TITLE_POSITION, 18, TEXT)
        renderer.draw_text(state.held_buttons_label, HELD_BUTTONS_POSITION, 16, MUTED)

        if state.show_help:
            help_rows = (
                HELP_ROWS_WITH_RUMBLE
                if state.vibration_supported
                else HELP_ROWS_WITHOUT_RUMBLE
            )
            for line, position in help_rows:
                renderer.draw_text(line, position, 16, MUTED)
        else:
            renderer.draw_text(
                "Press BACK to show help again",
                HELP_HIDDEN_POSITION,
                16,
                MUTED,
            )

    renderer.draw_fps(FPS_POSITION)
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
