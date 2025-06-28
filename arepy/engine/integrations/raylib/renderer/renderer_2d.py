from os import PathLike
from typing import cast

import raylib as rl
from pyray import Camera2D as rlCamera2D
from pyray import Vector2 as rlVector2

from arepy.bundle.components.camera import Camera2D
from arepy.engine.renderer import ArepyTexture, Color, Rect, TextureFilter


def create_render_texture(width: int, height: int) -> ArepyTexture:
    """
    Create a render texture.

    Args:
        width (int): The width of the render texture.
        height (int): The height of the render texture.

    Returns:
        ArepyTexture: The created render texture.
    """
    render_texture = rl.LoadRenderTexture(width, height)
    arepy_texture = ArepyTexture(render_texture.texture.id, (width, height))
    arepy_texture._ref_texture = render_texture.texture
    arepy_texture._ref_render_texture = render_texture
    set_texture_filter(arepy_texture, arepy_texture._filter)
    return arepy_texture


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
    arepy_texture._ref_texture = texture
    set_texture_filter(arepy_texture, arepy_texture._filter)
    return arepy_texture


def unload_texture(texture: ArepyTexture) -> None:
    """
    Unload a texture.

    Args:
        texture (ArepyTexture): The texture to unload.
    """
    rl.UnloadTexture(texture._ref)  # type: ignore


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
        texture._ref_texture,  # type: ignore
        src_rect.to_tuple(),
        (dst_rect.x, dst_rect.y),
        (color.r, color.g, color.b, color.a),
    )


def draw_texture_ex(
    texture: ArepyTexture,
    src_rect: Rect,
    dst_rect: Rect,
    origin: tuple[float, float],
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
    rl.DrawTexturePro(
        texture._ref_texture,  # type: ignore
        src_rect.to_tuple(),
        dst_rect.to_tuple(),
        origin,
        rotation,
        (color.r, color.g, color.b, color.a),
    )


def draw_unfilled_circle(
    center: tuple[float, float], radius: float, color: Color
) -> None:
    """
    Draw an unfilled circle.

    Args:
        center (tuple[float, float]): The center of the circle.
        radius (float): The radius of the circle.
        color (Color): The color of the circle.
    """
    rl.DrawCircleLines(
        int(center[0]),
        int(center[1]),
        radius,
        (color.r, color.g, color.b, color.a),
    )


def draw_circle(center: tuple[float, float], radius: float, color: Color) -> None:
    """
    Draw a circle.

    Args:
        center (tuple[float, float]): The center of the circle.
        radius (float): The radius of the circle.
        color (Color): The color of the circle.
    """
    rl.DrawCircle(
        int(center[0]),
        int(center[1]),
        radius,
        (color.r, color.g, color.b, color.a),
    )


def bind_render_texture(texture: ArepyTexture) -> None:
    """
    Bind a render texture.

    Args:
        texture (ArepyTexture): The render texture to bind.
    """
    rl.BeginTextureMode(texture._ref_render_texture)  # type: ignore


def unbind_render_texture() -> None:
    """
    Unbind a render texture.
    """
    rl.EndTextureMode()


def draw_rectangle(rect: Rect, color: Color) -> None:
    """
    Draw a rectangle.

    Args:
        rect (Rect): The rectangle to draw.
        color (Color): The color to tint the rectangle.
    """

    rl.DrawRectangle(
        int(rect.x),
        int(rect.y),
        rect.width,
        rect.height,
        (color.r, color.g, color.b, color.a),
    )


def draw_rectangle_ex(rect: Rect, rotation: float, color: Color) -> None:
    """
    Draw a rectangle with rotation.

    Args:
        rect (Rect): The rectangle to draw.
        rotation (float): The rotation angle.
        color (Color): The color to tint the rectangle.
    """

    rl.DrawRectanglePro(
        (rect.x, rect.y, rect.width, rect.height),
        (rect.width or 2 / 2, rect.height or 2 / 2),
        rotation,
        (color.r, color.g, color.b, color.a),
    )


def draw_unfilled_rectangle(rect: Rect, color: Color) -> None:
    """
    Draw lines.

    Args:
        points (list[tuple[float, float]]): The points to draw lines between.
        color (Color): The color of the lines.
    """
    rl.DrawRectangleLines(
        int(rect.x),
        int(rect.y),
        rect.width,  # type: ignore
        rect.height,  # type: ignore
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


def draw_lines(points: list[tuple[float, float]], color: Color) -> None:
    """
    Draw lines.

    Args:
        points (list[tuple[float, float]]): The points to draw lines between.
        color (Color): The color of the lines.
    """
    if len(points) < 2:
        return
    rl.DrawLineStrip(
        [(int(p[0]), int(p[1])) for p in points],
        len(points),
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


def screen_to_world(
    position: tuple[float, float], camera: Camera2D
) -> tuple[float, float]:
    """
    Convert screen coordinates to world coordinates.

    Args:
        position (tuple[float, float]): The position to convert.
        camera (Camera2D): The camera to use for the conversion.

    Returns:
        tuple[float, float]: The converted position.
    """
    result = rl.GetScreenToWorld2D(
        (position[0], position[1]),
        camera._ref,  # type: ignore
    )
    return (result.x, result.y)


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
    rl.rlDrawRenderBatchActive()


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


def swap_buffers() -> None:
    """
    Swap the buffers.
    """
    rl.EndDrawing()


def set_texture_filter(texture: ArepyTexture, filter: TextureFilter):
    """
    Set the texture filter.

    Args:
        filter (TextureFilter): The texture filter to set.
    """
    texture_filter_map = {
        TextureFilter.NEAREST: rl.TEXTURE_FILTER_POINT,
        TextureFilter.BILINEAR: rl.TEXTURE_FILTER_BILINEAR,
        TextureFilter.TRILINEAR: rl.TEXTURE_FILTER_TRILINEAR,
    }
    rl.SetTextureFilter(texture._ref_texture, texture_filter_map[filter])  # type: ignore


# Camera methods
def add_camera(camera: Camera2D) -> None:
    """
    Add a camera.

    Args:
        camera (Camera2D): The camera to add.
    """
    if camera._ref is None:
        camera._ref = rlCamera2D(  # type: ignore
            rlVector2(camera.target.x, camera.target.y),
            rlVector2(camera.offset.x, camera.offset.y),
            camera.rotation,
            camera.zoom,
        )


def begin_camera_mode(camera: Camera2D) -> None:
    """
    Set the current camera.

    Args:
        camera (Camera2D): The camera to set as the current camera.
    """
    rl.BeginMode2D(camera._ref)  # type: ignore


def end_camera_mode() -> None:
    """
    Set the current camera.

    Args:
        camera (Camera2D): The camera to set as the current camera.
    """
    rl.EndMode2D()


def update_camera(camera: Camera2D) -> None:
    """
    Update the camera.

    Args:
        camera (Camera2D): The camera to update.
    """
    camera._ref.target = rlVector2(camera.target.x, camera.target.y)  # type: ignore
    camera._ref.offset = rlVector2(camera.offset.x, camera.offset.y)  # type: ignore
    camera._ref.rotation = camera.rotation  # type: ignore
    camera._ref.zoom = camera.zoom  # type: ignore
