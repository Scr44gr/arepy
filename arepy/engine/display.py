"""Public window and monitor management protocol for Arepy."""

from enum import IntEnum, IntFlag
from os import PathLike
from typing import Protocol, runtime_checkable


class CursorType(IntEnum):
    DEFAULT = 0
    ARROW = 1
    IBEAM = 2
    CROSSHAIR = 3
    POINTING_HAND = 4
    RESIZE_EW = 5
    RESIZE_NS = 6
    RESIZE_NWSE = 7
    RESIZE_NESW = 8
    RESIZE_ALL = 9
    NOT_ALLOWED = 10


class WindowFlag(IntFlag):
    VSYNC_HINT = 0x0040
    FULLSCREEN_MODE = 0x0002
    WINDOW_RESIZABLE = 0x0004
    WINDOW_UNDECORATED = 0x0008
    WINDOW_HIDDEN = 0x0080
    WINDOW_MINIMIZED = 0x0200
    WINDOW_MAXIMIZED = 0x0400
    WINDOW_UNFOCUSED = 0x0800
    WINDOW_TOPMOST = 0x1000
    WINDOW_ALWAYS_RUN = 0x0100
    WINDOW_TRANSPARENT = 0x0010
    WINDOW_HIGHDPI = 0x2000
    WINDOW_MOUSE_PASSTHROUGH = 0x4000
    MSAA_4X_HINT = 0x0020
    INTERLACED_HINT = 0x10000
    BORDERLESS_WINDOWED_MODE = 0x8000


@runtime_checkable
class Display(Protocol):
    """Protocol defining window, cursor, clipboard, and monitor operations.

    The engine registers one `Display` implementation as a shared resource,
    so systems and helpers can access window state through type-based injection.
    """

    def create_window(self, width: int, height: int, title: str) -> None:
        """Create the game window with the given size and title."""
        ...

    def window_should_close(self) -> bool:
        """Return whether the user requested the window to close."""
        ...

    def destroy_window(self) -> None:
        """Close the window and release its backend resources."""
        ...

    def set_window_size(self, width: int, height: int) -> None:
        """Resize the window in pixels."""
        ...

    def get_window_size(self) -> tuple[int, int]:
        """Return the current window size in pixels."""
        ...

    def get_window_position(self) -> tuple[int, int]:
        """Return the current window position on screen."""
        ...

    def toggle_fullscreen(self) -> None:
        """Switch between windowed and fullscreen modes."""
        ...

    def hide_cursor(self) -> None:
        """Hide the OS mouse cursor."""
        ...

    def show_cursor(self) -> None:
        """Show the OS mouse cursor."""
        ...

    def is_cursor_hidden(self) -> bool:
        """Return whether the mouse cursor is currently hidden."""
        ...

    def is_fullscreen(self) -> bool:
        """Return whether the window is currently fullscreen."""
        ...

    def set_window_title(self, title: str) -> None:
        """Change the current window title."""
        ...

    def set_window_icon(self, path: PathLike[str]) -> None:
        """Set the window icon from an image file path."""
        ...

    def set_window_position(self, x: int, y: int) -> None:
        """Move the window to a screen position."""
        ...

    def is_window_resized(self) -> bool:
        """Return whether the window size changed recently."""
        ...

    def set_window_min_size(self, width: int, height: int) -> None:
        """Set the minimum allowed window size."""
        ...

    def set_window_max_size(self, width: int, height: int) -> None:
        """Set the maximum allowed window size."""
        ...

    def set_window_state(self, flags: int) -> None:
        """Enable one or more backend window state flags."""
        ...

    def clear_window_state(self, flags: int) -> None:
        """Disable one or more backend window state flags."""
        ...

    def is_window_state(self, flag: int) -> bool:
        """Return whether a specific window state flag is active."""
        ...

    def maximize_window(self) -> None:
        """Maximize the window."""
        ...

    def minimize_window(self) -> None:
        """Minimize the window."""
        ...

    def restore_window(self) -> None:
        """Restore a minimized or maximized window."""
        ...

    def is_window_maximized(self) -> bool:
        """Return whether the window is maximized."""
        ...

    def is_window_minimized(self) -> bool:
        """Return whether the window is minimized."""
        ...

    def is_window_focused(self) -> bool:
        """Return whether the window currently has focus."""
        ...

    def set_window_focused(self) -> None:
        """Request focus for the window."""
        ...

    def is_window_hidden(self) -> bool:
        """Return whether the window is hidden."""
        ...

    def set_window_opacity(self, opacity: float) -> None:
        """Set the window opacity from 0.0 to 1.0."""
        ...

    def get_window_scale_dpi(self) -> tuple[float, float]:
        """Return the DPI scaling factors used by the current monitor."""
        ...

    def toggle_borderless(self) -> None:
        """Toggle borderless windowed mode."""
        ...

    def set_mouse_cursor(self, cursor: CursorType) -> None:
        """Change the visible mouse cursor shape."""
        ...

    def set_clipboard_text(self, text: str) -> None:
        """Copy text into the system clipboard."""
        ...

    def get_clipboard_text(self) -> str:
        """Read text from the system clipboard."""
        ...

    def get_monitor_count(self) -> int:
        """Return how many monitors are currently available."""
        ...

    def get_current_monitor(self) -> int:
        """Return the index of the monitor hosting the window."""
        ...

    def get_monitor_size(self, monitor: int) -> tuple[int, int]:
        """Return the size of a monitor in pixels."""
        ...

    def get_monitor_refresh_rate(self, monitor: int) -> int:
        """Return the refresh rate of a monitor in hertz."""
        ...

    def get_time(self) -> float:
        """Return the elapsed engine time in seconds from the backend clock."""
        ...
