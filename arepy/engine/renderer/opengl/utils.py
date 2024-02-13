def is_outside_screen(
    rectangle_position: tuple[float, float],
    rectangle_size: tuple[float, float],
    screen_size: tuple[int, int],
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
