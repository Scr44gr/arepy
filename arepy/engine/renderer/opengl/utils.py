from numpy import array, uint8

DEFAULT_TEXTURE_COORDS = (0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0)


def is_outside_screen(
    rectangle_position: tuple[float, float],
    rectangle_size: tuple[float, float],
    screen_size: tuple[float, float],
) -> bool:
    """Check if a rectangle is outside the screen.
    Args:
        x (int): The x position of the rectangle.
        y (int): The y position of the rectangle.
        width (int): The width of the rectangle.
        height (int): The height of the rectangle.
    Returns:
        bool: Whether the rectangle is outside the screen.
    """
    x, y = rectangle_position
    width, height = rectangle_size
    screen_width, screen_height = screen_size
    return x + width < 0 or x > screen_width or y + height < 0 or y > screen_height


def get_texture_coordinates(
    src_rect: tuple[float, float, float, float],
    src_dest: tuple[float, float, float, float],
) -> tuple[float, float, float, float, float, float, float, float]:
    """Get the texture coordinates.
    Args:
        texture (ArepyTexture): The texture.
        src_rect (tuple[w, h, x, y]): The source rectangle.
        src_dest (tuple[w, h, x, y]): The destination rectangle.
    Returns:
        tuple[float, float, float, float, float, float, float, float]: The texture coordinates.
    """
    texture_width, texture_height = src_dest[0], src_dest[1]
    w, h, x, y = src_rect
    return (
        x / texture_width,
        (y + h) / texture_height,
        (x + w) / texture_width,
        (y + h) / texture_height,
        (x + w) / texture_width,
        y / texture_height,
        x / texture_width,
        y / texture_height,
    )


def get_line_rgba_data(
    width: int, height: int, color: tuple[int, int, int, int]
) -> list[tuple[int, int, int, int]]:
    """Get the line rgba.
    Args:
        width (int): The width.
        height (int): The height.
        color (tuple[int, int, int, int]): The color.
    Returns:
        list[int]: The line rgba.
    """
    return array([color for _ in range(width * height)], dtype=uint8).tolist()


def enable_renderdoc():
    """Enable RenderDoc."""
    import ctypes

    try:
        renderdoc = ctypes.cdll.LoadLibrary(
            r"C:\Program Files\RenderDoc\renderdoc.dll"
        )  # Windows

        if renderdoc:
            renderdoc.RDCInitGlobalHook.argtypes = [ctypes.c_char_p]
            renderdoc.RDCInitGlobalHook.restype = ctypes.c_bool
            renderdoc.RDCInitGlobalHook(None)
    except:
        pass
