from os import PathLike
from typing import cast

import raylib as rl

from arepy.engine.renderer import ArepyTexture, Color, Rect


def create_texture(path: PathLike[str]) -> ArepyTexture:
    """
    Create a texture from a file path.

    Args:
        path (PathLike[str]): The path to the texture file.

    Returns:
        ArepyTexture: The created texture.
    """
    texture = rl.LoadTexture(str(path).encode("utf-8"))
    arepy_texture = ArepyTexture(texture.id, (texture.width, texture.height))
    arepy_texture._ref = texture
    return arepy_texture


def set_max_framerate(max_frame_rate: int) -> None:
    """
    Set the maximum framerate.

    Args:
        max_frame_rate (int): The maximum framerate.
    """
    rl.SetTargetFPS(max_frame_rate)


def draw_texture(
    texture: ArepyTexture, src_rect: Rect, dst_rect: Rect, color: Color
) -> None:
    """
    Draw a texture.

    Args:
        texture (ArepyTexture): The texture to draw.
        src_rect (Rect): The source rectangle.
        dst_rect (Rect): The destination rectangle.
        color (Color): The color to tint the texture.
    """
    # the rl.Texture doesnt exists in raylib(works in the pyray module)
    # texture._ref = cast(rl.Texture, texture._ref)
    rl.DrawTextureRec(
        texture._ref,  # type: ignore
        src_rect.to_tuple(),
        (dst_rect.x, dst_rect.y),
        (color.r, color.g, color.b, color.a),
    )


def draw_texture_ex(
    texture: ArepyTexture,
    src_rect: Rect,
    dst_rect: Rect,
    rotation: float,
    color: Color,
) -> None:
    """
    Draw a texture with extended parameters.

    Args:
        texture (ArepyTexture): The texture to draw.
        src_rect (Rect): The source rectangle.
        dst_rect (Rect): The destination rectangle.
        rotation (float): The rotation angle.
        color (Color): The color to tint the texture.
    """
    texture._ref = cast(rl.Texture, texture._ref)
    rl.DrawTexturePro(
        texture._ref,
        src_rect.to_tuple(),
        dst_rect.to_tuple(),
        (dst_rect.width or 2 / 2, dst_rect.height or 2 / 2),
        rotation,
        (color.r, color.g, color.b, color.a),
    )


def draw_rectangle(rect: Rect, color: Color) -> None:
    """
    Draw a rectangle.

    Args:
        rect (Rect): The rectangle to draw.
        color (Color): The color to tint the rectangle.
    """
    assert (
        rect.width is not None and rect.height is not None
    ), "Width and height must be set"
    rl.DrawRectangle(
        int(rect.x),
        int(rect.y),
        rect.width,
        rect.height,
        (color.r, color.g, color.b, color.a),
    )


def draw_text(
    text: str, position: tuple[float, float], font_size: int, color: Color
) -> None:
    """
    Draw text.

    Args:
        text (str): The text to draw.
        position (tuple[float, float]): The position to draw the text.
        font_size (int): The size of the font.
        color (Color): The color of the text.
    """
    rl.DrawText(
        text.encode("utf-8"),
        int(position[0]),
        int(position[1]),
        font_size,
        (color.r, color.g, color.b, color.a),
    )


def draw_fps(position: tuple[int, int]) -> None:
    """
    Draw the frames per second.

    Args:
        position (tuple[float, float]): The position to draw the text.
        font_size (int): The size of the font.
        color (Color): The color of the text.
    """
    rl.DrawFPS(
        position[0],
        position[1],
    )


def clear(color: Color) -> None:
    """
    Clear the screen with a color.

    Args:
        color (Color): The color to clear the screen with.
    """
    rl.ClearBackground((color.r, color.g, color.b, color.a))


def start_frame() -> None:
    """
    Start a frame.
    """
    rl.BeginDrawing()


def end_frame() -> None:
    """
    End a frame.
    """
    rl.EndDrawing()


def get_delta_time() -> float:
    """
    Get the time between frames.

    Returns:
        float: The time between frames.
    """
    return rl.GetFrameTime()


def get_framerate() -> int:
    """
    Get the current framerate.

    Returns:
        float: The current framerate.
    """
    return rl.GetFPS()
