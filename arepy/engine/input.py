from enum import Enum
from typing import Iterator, Protocol

from ..event_manager.event_manager import EventManager


class Key(Enum):

    A = 65
    B = 66
    C = 67
    D = 68
    E = 69
    F = 70
    G = 71
    H = 72
    I = 73
    J = 74
    K = 75
    L = 76
    M = 77
    N = 78
    O = 79
    P = 80
    Q = 81
    R = 82
    S = 83
    T = 84
    U = 85
    V = 86
    W = 87
    X = 88
    Y = 89
    Z = 90
    SPACE = 32
    NUM_0 = 48
    NUM_1 = 49
    NUM_2 = 50
    NUM_3 = 51
    NUM_4 = 52
    NUM_5 = 53
    NUM_6 = 54
    NUM_7 = 55
    NUM_8 = 56
    NUM_9 = 57
    NUMPAD_0 = 320
    NUMPAD_1 = 321
    NUMPAD_2 = 322
    NUMPAD_3 = 323
    NUMPAD_4 = 324
    NUMPAD_5 = 325
    NUMPAD_6 = 326
    NUMPAD_7 = 327
    NUMPAD_8 = 328
    NUMPAD_9 = 329
    LEFT_SHIFT = 340
    LEFT_CONTROL = 341
    LEFT_ALT = 342
    LEFT_SUPER = 343
    RIGHT_SHIFT = 344
    RIGHT_CONTROL = 345
    RIGHT_ALT = 346
    RIGHT_SUPER = 347
    ESCAPE = 256
    ENTER = 257
    TAB = 258
    BACKSPACE = 259
    INSERT = 260
    DELETE = 261
    RIGHT = 262
    LEFT = 263
    DOWN = 264
    UP = 265
    PAGE_UP = 266
    PAGE_DOWN = 267
    HOME = 268
    END = 269
    CAPS_LOCK = 280
    SCROLL_LOCK = 281
    NUM_LOCK = 282
    PRINT_SCREEN = 283
    PAUSE = 284
    F1 = 290
    F2 = 291
    F3 = 292
    F4 = 293
    F5 = 294
    F6 = 295
    F7 = 296
    F8 = 297
    F9 = 298
    F10 = 299
    F11 = 300
    F12 = 301


class MouseButton(Enum):
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2
    # 3-7 are extra mouse buttonsq
    BUTTON_4 = 3
    BUTTON_5 = 4
    BUTTON_6 = 5
    BUTTON_7 = 6
    BUTTON_8 = 7


class Input(Protocol):
    """Input repository interface."""

    def register_dispatchers(self) -> None:
        """Dispatch input events for the current frame."""

    def get_mouse_position(self) -> tuple[float, float]:
        """Get the mouse position in the window."""
        ...

    def get_mouse_delta(self) -> tuple[float, float]:
        """Get the mouse delta between frames."""
        ...

    def get_mouse_wheel_delta(self) -> float:
        """Get the mouse amount of scroll in the y-axis."""
        ...

    def pool_events(self) -> None:
        """Pool events."""
        ...

    @property
    def event_manager(self) -> EventManager:
        """Get the event manager."""
        ...

    @event_manager.setter
    def event_manager(self) -> EventManager:
        """Get the event manager."""
        ...
