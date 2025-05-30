from typing import Iterator

import raylib as rl

from arepy.engine.input import Key, MouseButton


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
    """Pool the events."""
    rl.PollInputEvents()
