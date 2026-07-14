"""Browser display adapter."""

from time import perf_counter

from js import arepyRuntime, document


def create_window(width: int, height: int, title: str) -> None:
    arepyRuntime.createWindow(width, height, title)


def window_should_close() -> bool:
    return bool(arepyRuntime.shouldClose())


def destroy_window() -> None:
    arepyRuntime.close()


def set_window_size(width: int, height: int) -> None:
    arepyRuntime.resize(width, height)


def get_window_size() -> tuple[int, int]:
    return (int(arepyRuntime.width()), int(arepyRuntime.height()))


def get_window_position() -> tuple[float, float]:
    return (0.0, 0.0)


def toggle_fullscreen() -> None:
    arepyRuntime.toggleFullscreen()


def hide_cursor() -> None:
    document.body.style.cursor = "none"


def show_cursor() -> None:
    document.body.style.cursor = "default"


def is_cursor_hidden() -> bool:
    return document.body.style.cursor == "none"


def is_fullscreen() -> bool:
    return bool(document.fullscreenElement)


def set_window_title(title: str) -> None:
    document.title = title


def set_window_icon(path: object) -> None:
    return None


def set_window_position(x: int, y: int) -> None:
    return None


def is_window_resized() -> bool:
    return False


def set_window_min_size(width: int, height: int) -> None:
    return None


def set_window_max_size(width: int, height: int) -> None:
    return None


def set_window_state(flags: int) -> None:
    return None


def clear_window_state(flags: int) -> None:
    return None


def is_window_state(flag: int) -> bool:
    return False


def maximize_window() -> None:
    return None


def minimize_window() -> None:
    return None


def restore_window() -> None:
    return None


def is_window_maximized() -> bool:
    return False


def is_window_minimized() -> bool:
    return False


def is_window_focused() -> bool:
    return bool(document.hasFocus())


def set_window_focused() -> None:
    arepyRuntime.focus()


def is_window_hidden() -> bool:
    return bool(document.hidden)


def set_window_opacity(opacity: float) -> None:
    arepyRuntime.setOpacity(opacity)


def get_window_scale_dpi() -> tuple[float, float]:
    scale = float(arepyRuntime.devicePixelRatio())
    return (scale, scale)


def toggle_borderless() -> None:
    return None


def set_mouse_cursor(cursor: int) -> None:
    return None


def set_clipboard_text(text: str) -> None:
    arepyRuntime.setClipboardText(text)


def get_clipboard_text() -> str:
    return ""


def get_monitor_count() -> int:
    return 1


def get_current_monitor() -> int:
    return 0


def get_monitor_size(monitor: int) -> tuple[int, int]:
    return (int(arepyRuntime.screenWidth()), int(arepyRuntime.screenHeight()))


def get_monitor_refresh_rate(monitor: int) -> int:
    return 60


def get_time() -> float:
    return perf_counter()
