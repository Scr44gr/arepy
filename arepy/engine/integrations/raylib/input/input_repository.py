from typing import Iterator

import raylib as rl

from arepy.engine.input import (
    GamepadAxis,
    GamepadButton,
    GamepadDeviceType,
    Key,
    MouseButton,
)

_MAX_GAMEPADS = 4

_XBOX_DEVICE_MARKERS = (
    "XBOX",
    "X-BOX",
    "XINPUT",
    "MICROSOFT",
    "360 CONTROLLER",
)

_PLAYSTATION_DEVICE_MARKERS = (
    "PLAYSTATION",
    "PLAY STATION",
    "DUALSENSE",
    "DUALSENSE EDGE",
    "DUALSHOCK",
    "SONY",
    "PS3",
    "PS4",
    "PS5",
)

_NINTENDO_DEVICE_MARKERS = (
    "NINTENDO",
    "JOY-CON",
    "JOYCON",
    "PRO CONTROLLER",
    "SWITCH",
)

_GAMEPAD_VIBRATION_WARNING_MARKERS = (
    "gamepad",
    "vibration",
    "not available on target platform",
)

_gamepad_vibration_support_cache: tuple[int, bool] | None = None


def _coerce_gamepad_name(raw_name: object) -> str | None:
    if raw_name is None:
        return None
    if isinstance(raw_name, bytes):
        name = raw_name.decode("utf-8", errors="replace")
    else:
        name = str(raw_name)
    return name or None


def _classify_gamepad_name(name: str | None) -> GamepadDeviceType:
    if not name:
        return GamepadDeviceType.UNKNOWN

    normalized_name = name.upper()
    if normalized_name == "WIRELESS CONTROLLER":
        return GamepadDeviceType.PLAYSTATION
    if any(marker in normalized_name for marker in _XBOX_DEVICE_MARKERS):
        return GamepadDeviceType.XBOX
    if any(marker in normalized_name for marker in _PLAYSTATION_DEVICE_MARKERS):
        return GamepadDeviceType.PLAYSTATION
    if any(marker in normalized_name for marker in _NINTENDO_DEVICE_MARKERS):
        return GamepadDeviceType.NINTENDO
    return GamepadDeviceType.GENERIC


def _is_gamepad_vibration_backend_supported() -> bool:
    global _gamepad_vibration_support_cache

    current_backend_id = id(rl)
    if (
        _gamepad_vibration_support_cache is not None
        and _gamepad_vibration_support_cache[0] == current_backend_id
    ):
        return _gamepad_vibration_support_cache[1]

    try:
        ffi = rl.ffi
    except AttributeError:
        ffi = None

    try:
        set_trace_log_callback = rl.SetTraceLogCallback
    except AttributeError:
        set_trace_log_callback = None

    if ffi is None or set_trace_log_callback is None:
        _gamepad_vibration_support_cache = (current_backend_id, True)
        return True

    messages: list[str] = []

    @ffi.callback("void(int, char *, void *)")
    def trace_log_callback(_log_type: int, text: object, _args: object) -> None:
        try:
            messages.append(ffi.string(text).decode("utf-8", errors="replace"))
        except Exception:
            messages.append("")

    set_trace_log_callback(trace_log_callback)
    try:
        rl.SetGamepadVibration(0, 0.0, 0.0, 0.0)
    finally:
        set_trace_log_callback(ffi.NULL)

    is_supported = not any(
        all(marker in message.lower() for marker in _GAMEPAD_VIBRATION_WARNING_MARKERS)
        for message in messages
    )
    _gamepad_vibration_support_cache = (current_backend_id, is_supported)
    return is_supported


def is_key_pressed(key: Key) -> bool:
    """Check if a key is pressed."""
    return rl.IsKeyPressed(key.value)


def is_key_down(key: Key) -> bool:
    """Check if a key is down."""
    return rl.IsKeyDown(key.value)


def is_key_released(key: Key) -> bool:
    """Check if a key is released.

    Args:
        key (Key): The key to check.

    Returns:
        bool: True if the key is released.
    """
    return rl.IsKeyReleased(key.value)


def is_key_up(key: Key) -> bool:
    """Check if a key is up.

    Args:
        key (Key): The key to check.

    Returns:
        bool: True if the key is up.
    """
    return rl.IsKeyUp(key.value)


def get_keys_pressed() -> Iterator[Key]:
    """Get the keys that are pressed."""
    while (key := rl.GetKeyPressed()) != 0:
        yield Key(key)


def get_char_pressed() -> int:
    return rl.GetCharPressed()


def get_available_gamepads() -> tuple[int, ...]:
    """Get the IDs for the currently connected gamepads."""
    return tuple(
        gamepad_id
        for gamepad_id in range(_MAX_GAMEPADS)
        if rl.IsGamepadAvailable(gamepad_id)
    )


def is_gamepad_available(gamepad_id: int = 0) -> bool:
    """Check if a gamepad is available."""
    return rl.IsGamepadAvailable(gamepad_id)


def get_gamepad_name(gamepad_id: int = 0) -> str | None:
    """Get the backend-reported name for a connected gamepad."""
    if not is_gamepad_available(gamepad_id):
        return None
    return _coerce_gamepad_name(rl.GetGamepadName(gamepad_id))


def get_gamepad_device_type(gamepad_id: int = 0) -> GamepadDeviceType:
    """Get the coarse device family for a connected gamepad."""
    return _classify_gamepad_name(get_gamepad_name(gamepad_id))


def get_gamepad_axis_count(gamepad_id: int = 0) -> int:
    """Get the number of analog axes for a connected gamepad."""
    if not is_gamepad_available(gamepad_id):
        return 0
    return rl.GetGamepadAxisCount(gamepad_id)


def is_gamepad_button_pressed(
    button: GamepadButton, gamepad_id: int = 0
) -> bool:
    """Check if a gamepad button is pressed."""
    return rl.IsGamepadButtonPressed(gamepad_id, button.value)


def is_gamepad_button_down(button: GamepadButton, gamepad_id: int = 0) -> bool:
    """Check if a gamepad button is down."""
    return rl.IsGamepadButtonDown(gamepad_id, button.value)


def is_gamepad_button_released(
    button: GamepadButton, gamepad_id: int = 0
) -> bool:
    """Check if a gamepad button is released."""
    return rl.IsGamepadButtonReleased(gamepad_id, button.value)


def is_gamepad_button_up(button: GamepadButton, gamepad_id: int = 0) -> bool:
    """Check if a gamepad button is up."""
    return rl.IsGamepadButtonUp(gamepad_id, button.value)


def get_gamepad_axis_movement(axis: GamepadAxis, gamepad_id: int = 0) -> float:
    """Get the analog value for a gamepad axis."""
    if not is_gamepad_available(gamepad_id):
        return 0.0
    return rl.GetGamepadAxisMovement(gamepad_id, axis.value)


def is_gamepad_vibration_supported(gamepad_id: int = 0) -> bool:
    """Check whether vibration can be attempted for a connected gamepad."""
    return is_gamepad_available(gamepad_id) and _is_gamepad_vibration_backend_supported()


def set_gamepad_vibration(
    left_motor: float,
    right_motor: float,
    duration_seconds: float,
    gamepad_id: int = 0,
) -> None:
    """Start a vibration pulse on a connected gamepad."""
    if not is_gamepad_vibration_supported(gamepad_id):
        return

    rl.SetGamepadVibration(
        gamepad_id,
        max(0.0, min(1.0, left_motor)),
        max(0.0, min(1.0, right_motor)),
        max(0.0, duration_seconds),
    )


def is_mouse_button_pressed(button: MouseButton) -> bool:
    """Check if a mouse button is pressed."""
    return rl.IsMouseButtonPressed(button.value)


def is_mouse_button_down(button: MouseButton) -> bool:
    """Check if a mouse button is down."""
    return rl.IsMouseButtonDown(button.value)


def is_mouse_button_released(button: MouseButton) -> bool:
    """Check if a mouse button is released."""
    return rl.IsMouseButtonReleased(button.value)


def is_mouse_button_up(button: MouseButton) -> bool:
    """Check if a mouse button is up."""
    return rl.IsMouseButtonUp(button.value)


def get_mouse_position() -> tuple[float, float]:
    """Get the mouse position in the window."""
    mouse_position = rl.GetMousePosition()
    return (mouse_position.x, mouse_position.y)


def get_mouse_delta() -> tuple[float, float]:
    """Get the mouse delta between frames."""
    mouse_delta = rl.GetMouseDelta()
    return (mouse_delta.x, mouse_delta.y)


def get_mouse_wheel_delta() -> float:
    """Get the mouse wheel delta."""
    return rl.GetMouseWheelMove()


def set_exit_key(key: Key) -> None:
    """Set the exit key.

    Args:
        key (Key): The key to set as the exit key.
    """
    rl.SetExitKey(key.value)


def pool_events() -> None:
    """Poll the events."""
    rl.PollInputEvents()
