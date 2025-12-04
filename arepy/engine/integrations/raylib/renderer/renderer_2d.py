from os import PathLike
from typing import Optional, cast

import raylib as rl
from pyray import Camera2D as rlCamera2D
from pyray import Vector2 as rlVector2

from arepy.bundle.components.camera import Camera2D
from arepy.engine.renderer import ArepyFont, ArepyTexture, Color, Rect, TextureFilter


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


def set_mouse_position(position: tuple[float, float]) -> None:
    """
    Set the mouse position.

    Args:
        position (tuple[float, float]): The position to set the mouse to.
    """
    rl.SetMousePosition(int(position[0]), int(position[1]))


def disable_mouse_cursor() -> None:
    """
    Disable the mouse cursor.
    """
    rl.HideCursor()


def enable_mouse_cursor() -> None:
    """
    Enable the mouse cursor.
    """
    rl.ShowCursor()


def is_mouse_cursor_hidden() -> bool:
    """
    Check if the mouse cursor is hidden.

    Returns:
        bool: True if the mouse cursor is hidden, False otherwise.
    """
    return rl.IsCursorHidden()


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


def draw_rectangle_rounded(
    rect: Rect, roundness: float, segments: int, color: Color
) -> None:
    rl.DrawRectangleRounded(
        (rect.x, rect.y, rect.width, rect.height),
        roundness,
        segments,
        (color.r, color.g, color.b, color.a),
    )


def draw_rectangle_rounded_lines(
    rect: Rect, roundness: float, segments: int, color: Color
) -> None:
    rl.DrawRectangleRoundedLinesEx(
        (rect.x, rect.y, rect.width, rect.height),
        roundness,
        segments,
        1.0,
        (color.r, color.g, color.b, color.a),
    )


def draw_rectangle_lines_ex(rect: Rect, line_thickness: float, color: Color) -> None:
    rl.DrawRectangleLinesEx(
        (rect.x, rect.y, rect.width, rect.height),
        line_thickness,
        (color.r, color.g, color.b, color.a),
    )


def draw_line_ex(
    start: tuple[float, float],
    end: tuple[float, float],
    thickness: float,
    color: Color,
) -> None:
    rl.DrawLineEx(
        (start[0], start[1]),
        (end[0], end[1]),
        thickness,
        (color.r, color.g, color.b, color.a),
    )


def begin_scissor_mode(x: int, y: int, width: int, height: int) -> None:
    rl.BeginScissorMode(x, y, width, height)


def end_scissor_mode() -> None:
    rl.EndScissorMode()


def measure_text(text: str, font_size: int) -> int:
    return rl.MeasureText(text.encode("utf-8"), font_size)


def load_font_ex(
    path: PathLike[str],
    base_size: int,
    codepoints: Optional[list[int]],
    count: int,
) -> ArepyFont:
    font = rl.LoadFontEx(
        str(path).encode("utf-8"),
        base_size,
        codepoints,
        count,
    )
    arepy_font = ArepyFont(base_size)
    arepy_font._ref_font = font
    return arepy_font


def get_font_default() -> ArepyFont:
    font = rl.GetFontDefault()
    arepy_font = ArepyFont(font.baseSize)
    arepy_font._ref_font = font
    return arepy_font


def unload_font(font: ArepyFont) -> None:
    rl.UnloadFont(font._ref_font)  # type: ignore


def measure_text_ex(
    font: ArepyFont, text: str, font_size: float, spacing: float
) -> tuple[float, float]:
    result = rl.MeasureTextEx(
        font._ref_font,  # type: ignore
        text.encode("utf-8"),
        font_size,
        spacing,
    )
    return (result.x, result.y)


def draw_text_ex(
    font: ArepyFont,
    text: str,
    position: tuple[float, float],
    font_size: float,
    spacing: float,
    color: Color,
) -> None:
    rl.DrawTextEx(
        font._ref_font,  # type: ignore
        text.encode("utf-8"),
        (position[0], position[1]),
        font_size,
        spacing,
        (color.r, color.g, color.b, color.a),
    )


# Additional shape drawing functions


def draw_circle_lines(
    center: tuple[float, float], radius: float, color: Color
) -> None:
    """
    Draw circle outline.

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


def draw_ellipse(
    center: tuple[float, float],
    radius_h: float,
    radius_v: float,
    color: Color,
) -> None:
    """
    Draw a filled ellipse.

    Args:
        center (tuple[float, float]): The center of the ellipse.
        radius_h (float): The horizontal radius.
        radius_v (float): The vertical radius.
        color (Color): The color of the ellipse.
    """
    rl.DrawEllipse(
        int(center[0]),
        int(center[1]),
        radius_h,
        radius_v,
        (color.r, color.g, color.b, color.a),
    )


def draw_ellipse_lines(
    center: tuple[float, float],
    radius_h: float,
    radius_v: float,
    color: Color,
) -> None:
    """
    Draw ellipse outline.

    Args:
        center (tuple[float, float]): The center of the ellipse.
        radius_h (float): The horizontal radius.
        radius_v (float): The vertical radius.
        color (Color): The color of the ellipse.
    """
    rl.DrawEllipseLines(
        int(center[0]),
        int(center[1]),
        radius_h,
        radius_v,
        (color.r, color.g, color.b, color.a),
    )


def draw_triangle(
    v1: tuple[float, float],
    v2: tuple[float, float],
    v3: tuple[float, float],
    color: Color,
) -> None:
    """
    Draw a filled triangle.

    Args:
        v1 (tuple[float, float]): First vertex.
        v2 (tuple[float, float]): Second vertex.
        v3 (tuple[float, float]): Third vertex.
        color (Color): The color of the triangle.
    """
    rl.DrawTriangle(
        (v1[0], v1[1]),
        (v2[0], v2[1]),
        (v3[0], v3[1]),
        (color.r, color.g, color.b, color.a),
    )


def draw_triangle_lines(
    v1: tuple[float, float],
    v2: tuple[float, float],
    v3: tuple[float, float],
    color: Color,
) -> None:
    """
    Draw triangle outline.

    Args:
        v1 (tuple[float, float]): First vertex.
        v2 (tuple[float, float]): Second vertex.
        v3 (tuple[float, float]): Third vertex.
        color (Color): The color of the triangle.
    """
    rl.DrawTriangleLines(
        (v1[0], v1[1]),
        (v2[0], v2[1]),
        (v3[0], v3[1]),
        (color.r, color.g, color.b, color.a),
    )


def draw_poly(
    center: tuple[float, float],
    sides: int,
    radius: float,
    rotation: float,
    color: Color,
) -> None:
    """
    Draw a regular polygon (filled).

    Args:
        center (tuple[float, float]): The center of the polygon.
        sides (int): Number of sides.
        radius (float): The radius of the polygon.
        rotation (float): Rotation angle in degrees.
        color (Color): The color of the polygon.
    """
    rl.DrawPoly(
        (center[0], center[1]),
        sides,
        radius,
        rotation,
        (color.r, color.g, color.b, color.a),
    )


def draw_poly_lines(
    center: tuple[float, float],
    sides: int,
    radius: float,
    rotation: float,
    color: Color,
) -> None:
    """
    Draw a regular polygon outline.

    Args:
        center (tuple[float, float]): The center of the polygon.
        sides (int): Number of sides.
        radius (float): The radius of the polygon.
        rotation (float): Rotation angle in degrees.
        color (Color): The color of the polygon.
    """
    rl.DrawPolyLinesEx(
        (center[0], center[1]),
        sides,
        radius,
        rotation,
        1.0,
        (color.r, color.g, color.b, color.a),
    )


def draw_poly_lines_ex(
    center: tuple[float, float],
    sides: int,
    radius: float,
    rotation: float,
    line_thickness: float,
    color: Color,
) -> None:
    """
    Draw a regular polygon outline with extended parameters.

    Args:
        center (tuple[float, float]): The center of the polygon.
        sides (int): Number of sides.
        radius (float): The radius of the polygon.
        rotation (float): Rotation angle in degrees.
        line_thickness (float): The thickness of the lines.
        color (Color): The color of the polygon.
    """
    rl.DrawPolyLinesEx(
        (center[0], center[1]),
        sides,
        radius,
        rotation,
        line_thickness,
        (color.r, color.g, color.b, color.a),
    )


def draw_ring(
    center: tuple[float, float],
    inner_radius: float,
    outer_radius: float,
    start_angle: float,
    end_angle: float,
    segments: int,
    color: Color,
) -> None:
    """
    Draw a filled ring (donut shape).

    Args:
        center (tuple[float, float]): The center of the ring.
        inner_radius (float): Inner radius of the ring.
        outer_radius (float): Outer radius of the ring.
        start_angle (float): Start angle in degrees.
        end_angle (float): End angle in degrees.
        segments (int): Number of segments.
        color (Color): The color of the ring.
    """
    rl.DrawRing(
        (center[0], center[1]),
        inner_radius,
        outer_radius,
        start_angle,
        end_angle,
        segments,
        (color.r, color.g, color.b, color.a),
    )


def draw_ring_lines(
    center: tuple[float, float],
    inner_radius: float,
    outer_radius: float,
    start_angle: float,
    end_angle: float,
    segments: int,
    color: Color,
) -> None:
    """
    Draw ring outline.

    Args:
        center (tuple[float, float]): The center of the ring.
        inner_radius (float): Inner radius of the ring.
        outer_radius (float): Outer radius of the ring.
        start_angle (float): Start angle in degrees.
        end_angle (float): End angle in degrees.
        segments (int): Number of segments.
        color (Color): The color of the ring.
    """
    rl.DrawRingLines(
        (center[0], center[1]),
        inner_radius,
        outer_radius,
        start_angle,
        end_angle,
        segments,
        (color.r, color.g, color.b, color.a),
    )


def draw_line_bezier(
    start: tuple[float, float],
    end: tuple[float, float],
    thickness: float,
    color: Color,
) -> None:
    """
    Draw a cubic bezier line.

    Args:
        start (tuple[float, float]): Start position.
        end (tuple[float, float]): End position.
        thickness (float): Line thickness.
        color (Color): The color of the line.
    """
    rl.DrawLineBezier(
        (start[0], start[1]),
        (end[0], end[1]),
        thickness,
        (color.r, color.g, color.b, color.a),
    )


def draw_rectangle_gradient_v(
    rect: Rect,
    top_color: Color,
    bottom_color: Color,
) -> None:
    """
    Draw a rectangle with vertical gradient.

    Args:
        rect (Rect): The rectangle to draw.
        top_color (Color): Color at the top.
        bottom_color (Color): Color at the bottom.
    """
    rl.DrawRectangleGradientV(
        int(rect.x),
        int(rect.y),
        int(rect.width),
        int(rect.height),
        (top_color.r, top_color.g, top_color.b, top_color.a),
        (bottom_color.r, bottom_color.g, bottom_color.b, bottom_color.a),
    )


def draw_rectangle_gradient_h(
    rect: Rect,
    left_color: Color,
    right_color: Color,
) -> None:
    """
    Draw a rectangle with horizontal gradient.

    Args:
        rect (Rect): The rectangle to draw.
        left_color (Color): Color at the left.
        right_color (Color): Color at the right.
    """
    rl.DrawRectangleGradientH(
        int(rect.x),
        int(rect.y),
        int(rect.width),
        int(rect.height),
        (left_color.r, left_color.g, left_color.b, left_color.a),
        (right_color.r, right_color.g, right_color.b, right_color.a),
    )


def draw_rectangle_gradient_ex(
    rect: Rect,
    top_left: Color,
    bottom_left: Color,
    top_right: Color,
    bottom_right: Color,
) -> None:
    """
    Draw a rectangle with 4-corner gradient.

    Args:
        rect (Rect): The rectangle to draw.
        top_left (Color): Color at the top-left corner.
        bottom_left (Color): Color at the bottom-left corner.
        top_right (Color): Color at the top-right corner.
        bottom_right (Color): Color at the bottom-right corner.
    """
    rl.DrawRectangleGradientEx(
        (rect.x, rect.y, rect.width, rect.height),
        (top_left.r, top_left.g, top_left.b, top_left.a),
        (bottom_left.r, bottom_left.g, bottom_left.b, bottom_left.a),
        (top_right.r, top_right.g, top_right.b, top_right.a),
        (bottom_right.r, bottom_right.g, bottom_right.b, bottom_right.a),
    )


def draw_pixel(
    position: tuple[float, float],
    color: Color,
) -> None:
    """
    Draw a single pixel.

    Args:
        position (tuple[float, float]): Position of the pixel.
        color (Color): The color of the pixel.
    """
    rl.DrawPixel(
        int(position[0]),
        int(position[1]),
        (color.r, color.g, color.b, color.a),
    )
