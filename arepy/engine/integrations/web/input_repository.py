"""Browser input adapter."""

from typing import Iterator

from js import arepyRuntime

from arepy.engine.input import GamepadButton, GamepadDeviceType, Key, MouseButton


def is_key_pressed(key: Key) -> bool:
    return bool(arepyRuntime.keyPressed(key.value))


def is_key_down(key: Key) -> bool:
    return bool(arepyRuntime.keyDown(key.value))


def is_key_released(key: Key) -> bool:
    return bool(arepyRuntime.keyReleased(key.value))


def is_key_up(key: Key) -> bool:
    return not is_key_down(key)


def get_keys_pressed() -> Iterator[Key]:
    return iter(())


def get_char_pressed() -> int:
    return 0


def get_available_gamepads() -> tuple[int, ...]:
    return ()


def is_gamepad_available(gamepad_id: int = 0) -> bool:
    return False


def get_gamepad_name(gamepad_id: int = 0) -> str | None:
    return None


def get_gamepad_device_type(gamepad_id: int = 0) -> GamepadDeviceType:
    return GamepadDeviceType.UNKNOWN


def get_gamepad_axis_count(gamepad_id: int = 0) -> int:
    return 0


def is_gamepad_button_pressed(button: GamepadButton, gamepad_id: int = 0) -> bool:
    return False


is_gamepad_button_down = is_gamepad_button_pressed
is_gamepad_button_released = is_gamepad_button_pressed


def is_gamepad_button_up(button: GamepadButton, gamepad_id: int = 0) -> bool:
    return True


def get_gamepad_axis_movement(axis: object, gamepad_id: int = 0) -> float:
    return 0.0


def is_gamepad_vibration_supported(gamepad_id: int = 0) -> bool:
    return False


def set_gamepad_vibration(
    left_motor: float,
    right_motor: float,
    duration_seconds: float,
    gamepad_id: int = 0,
) -> None:
    return None


def is_mouse_button_pressed(button: MouseButton) -> bool:
    return bool(arepyRuntime.mousePressed(button.value))


def is_mouse_button_down(button: MouseButton) -> bool:
    return bool(arepyRuntime.mouseDown(button.value))


def is_mouse_button_released(button: MouseButton) -> bool:
    return bool(arepyRuntime.mouseReleased(button.value))


def is_mouse_button_up(button: MouseButton) -> bool:
    return not is_mouse_button_down(button)


def get_mouse_position() -> tuple[float, float]:
    return (float(arepyRuntime.mouseX()), float(arepyRuntime.mouseY()))


def get_mouse_delta() -> tuple[float, float]:
    return (0.0, 0.0)


def get_mouse_wheel_delta() -> float:
    return 0.0


def set_exit_key(key: Key) -> None:
    return None


def _finish_frame() -> None:
    arepyRuntime.finishInputFrame()


def pool_events() -> None:
    """Preserve the legacy public adapter behavior."""
    _finish_frame()
