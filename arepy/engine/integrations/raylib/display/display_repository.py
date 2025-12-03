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
    global window_size
    rl.glfwInit()
    rl.InitWindow(width, height, title.encode("utf-8"))
    window_size = (width, height)


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
    global window_size
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
    rl.SetConfigFlags(rl.FLAG_VSYNC_HINT if enabled else 0)


def is_window_resized() -> bool:
    return rl.IsWindowResized()


def set_window_min_size(width: int, height: int) -> None:
    rl.SetWindowMinSize(width, height)


def set_window_max_size(width: int, height: int) -> None:
    rl.SetWindowMaxSize(width, height)


def set_window_state(flags: int) -> None:
    rl.SetWindowState(flags)


def clear_window_state(flags: int) -> None:
    rl.ClearWindowState(flags)


def is_window_state(flag: int) -> bool:
    return rl.IsWindowState(flag)


def maximize_window() -> None:
    rl.MaximizeWindow()


def minimize_window() -> None:
    rl.MinimizeWindow()


def restore_window() -> None:
    rl.RestoreWindow()


def is_window_maximized() -> bool:
    return rl.IsWindowMaximized()


def is_window_minimized() -> bool:
    return rl.IsWindowMinimized()


def is_window_focused() -> bool:
    return rl.IsWindowFocused()


def set_window_focused() -> None:
    rl.SetWindowFocused()


def is_window_hidden() -> bool:
    return rl.IsWindowHidden()


def set_window_opacity(opacity: float) -> None:
    rl.SetWindowOpacity(opacity)


def get_window_scale_dpi() -> tuple[float, float]:
    scale = rl.GetWindowScaleDPI()
    return (scale.x, scale.y)


def toggle_borderless() -> None:
    rl.ToggleBorderlessWindowed()
