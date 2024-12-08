from os import PathLike
from os.path import exists

import raylib as rl

window_size: tuple[int, int]


def create_window(width: int, height: int, title: str) -> None:
    """
    Create a window.

    Args:
        width (int): The window width.
        height (int): The window height.
        title (str): The window title.
    """
    rl.glfwInit()
    rl.InitWindow(width, height, title.encode("utf-8"))


def window_should_close() -> bool:
    """
    Check if the window should close.

    Returns:
        bool: True if the window should close.
    """
    return rl.WindowShouldClose()


def destroy_window() -> None:
    """
    Destroy the window.
    """
    rl.CloseWindow()


def set_window_size(width: int, height: int) -> None:
    """
    Set the window size.

    Args:
        width (int): The window width.
        height (int): The window height.
    """
    global window_size
    window_size = (width, height)
    rl.SetWindowSize(width, height)


def get_window_size() -> tuple[int, int]:
    """
    Get the window size.

    Returns:
        tuple[int, int]: The window size.
    """
    return window_size


def get_window_position() -> tuple[float, float]:
    """
    Get the window position.

    Returns:
        tuple[int, int]: The window position.
    """
    position = rl.GetWindowPosition()
    return (position.x, position.y)


def toggle_fullscreen() -> None:
    """
    Toggle fullscreen mode.
    """
    rl.ToggleFullscreen()


def hide_cursor() -> None:
    """
    Hide the cursor.
    """
    rl.HideCursor()


def show_cursor() -> None:
    """
    Show the cursor.
    """
    rl.ShowCursor()


def is_cursor_hidden() -> bool:
    """
    Check if the cursor is hidden.

    Returns:
        bool: True if the cursor is hidden.
    """
    return rl.IsCursorHidden()


def is_fullscreen() -> bool:
    """
    Check if the window is fullscreen.

    Returns:
        bool: True if the window is fullscreen.
    """
    return rl.IsWindowFullscreen()


def set_window_title(title: str) -> None:
    """
    Set the window title.

    Args:
        title (str): The window title.
    """
    rl.SetWindowTitle(title.encode("utf-8"))


def set_window_icon(path: PathLike[str]) -> None:
    """
    Set the window icon.

    Args:
        path (str): The path to the icon.
    """
    if not exists(path):
        raise FileNotFoundError(f"Icon file not found: {path}")

    icon = rl.LoadImage(str(path).encode("utf-8"))
    rl.SetWindowIcon(icon)


def set_window_position(x: int, y: int) -> None:
    """
    Set the window position.

    Args:
        x: (int): The x position.
        y (int): The y position.
    """
    rl.SetWindowPosition(x, y)


def set_vsync(enabled: bool) -> None:
    """SHOULD CALL BEFORE `create_window`

    Set vsync.

    Args:
        enabled (bool): True if vsync should be enabled.
    """
    rl.SetConfigFlags(rl.FLAG_VSYNC_HINT if enabled else 0)
