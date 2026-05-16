"""Public input protocol and enums for keyboard, mouse, and gamepad state."""

from enum import Enum
from typing import Iterator, Protocol, runtime_checkable

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
    EQUAL = 61
    LEFT_BRACKET = 91
    RIGHT_BRACKET = 93
    BACKSLASH = 92
    SEMICOLON = 59
    APOSTROPHE = 39
    GRAVE_ACCENT = 96
    COMMA = 44
    PERIOD = 46
    SLASH = 47
    MINUS = 45

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


class GamepadButton(Enum):
    UNKNOWN = 0
    DPAD_UP = 1
    DPAD_RIGHT = 2
    DPAD_DOWN = 3
    DPAD_LEFT = 4
    FACE_UP = 5
    FACE_RIGHT = 6
    FACE_DOWN = 7
    FACE_LEFT = 8
    LEFT_SHOULDER = 9
    LEFT_TRIGGER = 10
    RIGHT_SHOULDER = 11
    RIGHT_TRIGGER = 12
    BACK = 13
    HOME = 14
    START = 15
    LEFT_STICK = 16
    RIGHT_STICK = 17


class GamepadAxis(Enum):
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_TRIGGER = 4
    RIGHT_TRIGGER = 5


class GamepadDeviceType(Enum):
    UNKNOWN = "unknown"
    GENERIC = "generic"
    XBOX = "xbox"
    PLAYSTATION = "playstation"
    NINTENDO = "nintendo"


@runtime_checkable
class Input(Protocol):
    """Protocol defining keyboard, mouse, and gamepad input queries.

    The engine registers one `Input` implementation as a shared resource,
    so systems can inspect player input through type-based injection.
    """

    def is_key_pressed(self, key: Key) -> bool:
        """Check if a key is pressed."""
        ...

    def is_key_down(self, key: Key) -> bool:
        """Check if a key is down."""
        ...

    def is_key_released(self, key: Key) -> bool:
        """Check if a key is released.

        Args:
            key (Key): The key to check.

        Returns:
            bool: True if the key is released.
        """
        ...

    def is_key_up(self, key: Key) -> bool:
        """Check if a key is up.

        Args:
            key (Key): The key to check.

        Returns:
            bool: True if the key is up.
        """
        ...

    def get_keys_pressed(self) -> Iterator[Key]:
        """Iterate over keys pressed during the current polling step."""
        ...

    def get_char_pressed(self) -> int:
        """Return the next typed Unicode codepoint, or a backend-specific empty value."""
        ...

    def get_available_gamepads(self) -> tuple[int, ...]:
        """Return the IDs for the gamepads currently connected to the backend."""
        ...

    def is_gamepad_available(self, gamepad_id: int = 0) -> bool:
        """Check if a gamepad is available.

        Args:
            gamepad_id (int): The backend gamepad slot to inspect.

        Returns:
            bool: True if the requested gamepad is connected.
        """
        ...

    def get_gamepad_name(self, gamepad_id: int = 0) -> str | None:
        """Return the backend-reported name for a connected gamepad.

        Args:
            gamepad_id (int): The backend gamepad slot to inspect.

        Returns:
            str | None: The gamepad name, or None if the slot is unavailable.
        """
        ...

    def get_gamepad_device_type(
        self, gamepad_id: int = 0
    ) -> GamepadDeviceType:
        """Return a coarse device family for a connected gamepad.

        Args:
            gamepad_id (int): The backend gamepad slot to inspect.

        Returns:
            GamepadDeviceType: The detected device family.
        """
        ...

    def get_gamepad_axis_count(self, gamepad_id: int = 0) -> int:
        """Return the number of analog axes reported by a gamepad."""
        ...

    def is_gamepad_button_pressed(
        self, button: GamepadButton, gamepad_id: int = 0
    ) -> bool:
        """Check if a gamepad button was pressed during the current frame."""
        ...

    def is_gamepad_button_down(
        self, button: GamepadButton, gamepad_id: int = 0
    ) -> bool:
        """Check if a gamepad button is currently held down."""
        ...

    def is_gamepad_button_released(
        self, button: GamepadButton, gamepad_id: int = 0
    ) -> bool:
        """Check if a gamepad button was released during the current frame."""
        ...

    def is_gamepad_button_up(
        self, button: GamepadButton, gamepad_id: int = 0
    ) -> bool:
        """Check if a gamepad button is currently up."""
        ...

    def get_gamepad_axis_movement(
        self, axis: GamepadAxis, gamepad_id: int = 0
    ) -> float:
        """Return the current analog value for a gamepad axis."""
        ...

    def is_gamepad_vibration_supported(self, gamepad_id: int = 0) -> bool:
        """Return whether vibration can be attempted for a connected gamepad.

        Args:
            gamepad_id (int): The backend gamepad slot to inspect.

        Returns:
            bool: True when the current backend can attempt vibration for the slot.
        """
        ...

    def set_gamepad_vibration(
        self,
        left_motor: float,
        right_motor: float,
        duration_seconds: float,
        gamepad_id: int = 0,
    ) -> None:
        """Start a vibration pulse on a connected gamepad.

        Args:
            left_motor (float): Intensity for the low-frequency motor in the range [0, 1].
            right_motor (float): Intensity for the high-frequency motor in the range [0, 1].
            duration_seconds (float): Pulse duration in seconds.
            gamepad_id (int): The backend gamepad slot to target.
        """
        ...

    def is_mouse_button_pressed(self, button: MouseButton) -> bool:
        """Check if a mouse button is pressed."""
        ...

    def is_mouse_button_down(self, button: MouseButton) -> bool:
        """Check if a mouse button is down."""
        ...

    def is_mouse_button_released(self, button: MouseButton) -> bool:
        """Check if a mouse button is released."""
        ...

    def is_mouse_button_up(self, button: MouseButton) -> bool:
        """Check if a mouse button is up."""
        ...

    def get_mouse_position(self) -> tuple[float, float]:
        """Get the mouse position in the window."""
        ...

    def get_mouse_delta(self) -> tuple[float, float]:
        """Get the mouse delta between frames."""
        ...

    def get_mouse_wheel_delta(self) -> float:
        """Return vertical mouse-wheel movement since the previous frame."""
        ...

    def set_exit_key(self, key: Key) -> None:
        """Set the keyboard shortcut that closes the window."""
        ...

    def pool_events(self) -> None:
        """Poll the backend for fresh input events."""
        ...
