import sys
from sys import stdout
from typing import Iterator

import raylib as rl
from raylib import ffi

from .....event_manager.event_manager import EventManager
from .....event_manager.handlers.input_event_handler import (
    ClearEvents,
    Key,
    KeyboardPressedEvent,
    KeyboardReleasedEvent,
    MouseMovedEvent,
    MousePressedEvent,
    MouseReleasedEvent,
    MouseWheelEvent,
)
from ....input import Key, MouseButton

PRESS = 1
RELEASE = 0
REPEAT = 2

event_manager: EventManager = None  # type: ignore


@ffi.callback("void(int, const char *)")
def ErrorCallback(error: int, description: bytes):
    print("%r" % description, file=sys.stderr)


rl.glfwSetErrorCallback(ErrorCallback)  # type: ignore


@ffi.callback("void(GLFWwindow *, int, int, int, int)")
def keyboard_callback(window, key, scancode, action, mods):
    if action == PRESS:
        event_manager.emit(KeyboardPressedEvent(Key(key)))
    elif action == RELEASE:
        event_manager.emit(KeyboardReleasedEvent(Key(key)))


@ffi.callback("void(GLFWwindow*, double, double)")
def mouse_callback(window, x, y):
    event_manager.emit(MouseMovedEvent(x, y))


@ffi.callback("void(GLFWwindow*, int, int, int)")
def mouse_button_callback(window, button, action, mods):
    if action == PRESS:
        event_manager.emit(MousePressedEvent(MouseButton(button)))
    elif action == RELEASE:
        event_manager.emit(MouseReleasedEvent(MouseButton(button)))


@ffi.callback("void(GLFWwindow*, double, double)")
def resize_callback(window, width, height):
    pass


@ffi.callback("void(GLFWwindow*, double, double)")
def scroll_callback(window, x_offset, y_offset):
    event_manager.emit(MouseWheelEvent(x_offset, y_offset))


@ffi.callback("void(GLFWwindow*, unsigned int)")
def char_callback(window, char):
    pass


def register_dispatchers() -> None:
    """Dispatch input events for the current frame."""
    assert event_manager is not None, "Event manager is not set."

    window = rl.glfwGetCurrentContext()
    rl.glfwSetKeyCallback(window, keyboard_callback)
    rl.glfwSetCursorPosCallback(window, mouse_callback)
    rl.glfwSetMouseButtonCallback(window, mouse_button_callback)
    rl.glfwSetScrollCallback(window, scroll_callback)
    rl.glfwSetCharCallback(window, char_callback)


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


def pool_events() -> None:
    """Pool the events."""
    rl.PollInputEvents()
