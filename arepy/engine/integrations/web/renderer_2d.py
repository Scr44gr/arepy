"""Canvas-backed 2D renderer for Pyodide builds."""

from __future__ import annotations

from os import PathLike
from time import perf_counter
from typing import TYPE_CHECKING, Optional

import numpy as np
from numpy.typing import NDArray
from js import arepyRuntime

from arepy.engine.renderer import (
    ArepyFont,
    ArepyShader,
    ArepyTexture,
    Color,
    Rect,
    TextureFilter,
)
from arepy.engine.renderer.texture_atlas import (
    TextureAtlas,
    TextureAtlasCollection,
    TextureAtlasRegion,
    TextureBatchLayout,
)

if TYPE_CHECKING:
    from arepy.asset_store import AssetStore

_next_texture_id = 1
_delta_time = 1.0 / 60.0
_last_frame_time = perf_counter()
_framerate = 60
_BLACK = Color(0, 0, 0, 255)
_batch_buffers: dict[int, NDArray[np.float32]] = {}


def create_texture(path: PathLike[str]) -> ArepyTexture:
    global _next_texture_id
    logical_path = _normalize_path(path)
    image = arepyRuntime.getImage(logical_path)
    if image is None:
        raise FileNotFoundError(f"Web image was not preloaded: {logical_path}")
    texture = ArepyTexture(
        _next_texture_id,
        (int(image.width), int(image.height)),
    )
    texture._ref_texture = image
    _next_texture_id += 1
    return texture


def unload_texture(texture: ArepyTexture) -> None:
    texture._ref_texture = None


def build_texture_atlas(
    asset_store: "AssetStore",
    *,
    max_size: tuple[int, int] = (2048, 2048),
    padding: int = 1,
) -> TextureAtlasCollection:
    _batch_buffers.clear()
    atlases: list[TextureAtlas] = []
    regions: dict[str, TextureAtlasRegion] = {}
    for index, (asset_id, texture) in enumerate(asset_store.textures.items()):
        width, height = texture.get_size()
        atlases.append(TextureAtlas(texture, index, (width, height)))
        regions[asset_id] = TextureAtlasRegion(index, 0, 0, width, height)
    return TextureAtlasCollection(tuple(atlases), regions)


def draw_texture(
    texture: ArepyTexture,
    source: Rect,
    dest: Rect,
    color: Color,
) -> None:
    arepyRuntime.drawImage(
        texture._ref_texture,
        source.x,
        source.y,
        source.width,
        source.height,
        dest.x,
        dest.y,
        dest.width,
        dest.height,
        color.r,
        color.g,
        color.b,
        color.a,
    )


def draw_texture_ex(
    texture: ArepyTexture,
    source: Rect,
    dest: Rect,
    origin: tuple[float, float],
    rotation: float,
    color: Color,
) -> None:
    arepyRuntime.drawImageEx(
        texture._ref_texture,
        source.x,
        source.y,
        source.width,
        source.height,
        dest.x,
        dest.y,
        dest.width,
        dest.height,
        origin[0],
        origin[1],
        rotation,
        color.a,
    )


def draw_texture_batch(
    atlases: TextureAtlasCollection,
    layout: TextureBatchLayout,
    dest_x: object,
    dest_y: object,
    dest_width: object,
    dest_height: object,
    origin_x: object,
    origin_y: object,
    rotation: object,
    color: Color,
) -> None:
    for group in layout.groups:
        indices = group.entity_indices
        count = len(indices)
        buffer_key = id(group)
        packed = _batch_buffers.get(buffer_key)
        if packed is None or len(packed) != count:
            packed = np.empty((count, 11), dtype=np.float32)
            _batch_buffers[buffer_key] = packed

        packed[:, 0] = group.source_x
        packed[:, 1] = group.source_y
        packed[:, 2] = group.source_width
        packed[:, 3] = group.source_height
        if group.uses_dense_entity_order:
            packed[:, 4] = dest_x
            packed[:, 5] = dest_y
            packed[:, 6] = dest_width
            packed[:, 7] = dest_height
            packed[:, 8] = origin_x
            packed[:, 9] = origin_y
            packed[:, 10] = rotation
        else:
            packed[:, 4] = dest_x[indices]
            packed[:, 5] = dest_y[indices]
            packed[:, 6] = dest_width[indices]
            packed[:, 7] = dest_height[indices]
            packed[:, 8] = origin_x[indices]
            packed[:, 9] = origin_y[indices]
            packed[:, 10] = rotation[indices]
        arepyRuntime.drawBatchPacked(
            group.texture._ref_texture,
            packed,
            color.a,
        )


def draw_rectangle(rect: Rect, color: Color) -> None:
    arepyRuntime.fillRect(
        rect.x,
        rect.y,
        rect.width,
        rect.height,
        _css_color(color),
    )


def draw_text(
    text: str,
    position: tuple[float, float],
    font_size: int,
    color: Color,
) -> None:
    arepyRuntime.drawText(
        text,
        position[0],
        position[1],
        font_size,
        _css_color(color),
    )


def draw_fps(position: tuple[int, int]) -> None:
    draw_text(
        f"FPS: {_framerate}",
        position,
        20,
        _BLACK,
    )


def clear(color: Color) -> None:
    arepyRuntime.clear(_css_color(color))


def start_frame() -> None:
    return None


def end_frame() -> None:
    return None


def swap_buffers() -> None:
    global _delta_time, _framerate, _last_frame_time
    now = perf_counter()
    _delta_time = max(now - _last_frame_time, 1.0 / 1000.0)
    _last_frame_time = now
    _framerate = round(1.0 / _delta_time)
    arepyRuntime.finishFrame()


def get_delta_time() -> float:
    return _delta_time


def get_framerate() -> int:
    return _framerate


def set_max_framerate(max_frame_rate: int) -> None:
    return None


def set_texture_filter(texture: ArepyTexture, filter: TextureFilter) -> None:
    texture._filter = filter


def flush() -> None:
    return None


def measure_text(text: str, font_size: int) -> int:
    return int(arepyRuntime.measureText(text, font_size))


def get_font_default() -> ArepyFont:
    return ArepyFont(16)


def unload_font(font: ArepyFont) -> None:
    return None


def load_font_ex(
    path: PathLike[str],
    base_size: int,
    codepoints: Optional[list[int]],
    count: int,
) -> ArepyFont:
    return ArepyFont(base_size)


def measure_text_ex(
    font: ArepyFont,
    text: str,
    font_size: float,
    spacing: float,
) -> tuple[float, float]:
    return (float(measure_text(text, int(font_size))), float(font_size))


def create_render_texture(width: int, height: int) -> ArepyTexture:
    raise NotImplementedError("Render textures are not available in the web backend yet.")


def load_shader(
    vertex_path: Optional[PathLike[str]] = None,
    fragment_path: Optional[PathLike[str]] = None,
) -> ArepyShader:
    raise NotImplementedError("Custom shaders are not available in the web backend yet.")


compile_shader = load_shader


def unload_shader(shader: ArepyShader) -> None:
    _unsupported("unload_shader")


def begin_shader_mode(shader: ArepyShader) -> None:
    _unsupported("begin_shader_mode")


def end_shader_mode() -> None:
    _unsupported("end_shader_mode")


def set_shader_value(
    shader: ArepyShader,
    uniform_type: object,
    name: str,
    value: object,
) -> None:
    _unsupported("set_shader_value")


def bind_render_texture(texture: ArepyTexture) -> None:
    _unsupported("bind_render_texture")


def unbind_render_texture() -> None:
    _unsupported("unbind_render_texture")


def draw_rectangle_ex(rect: Rect, rotation: float, color: Color) -> None:
    _unsupported("draw_rectangle_ex")


def draw_unfilled_rectangle(rect: Rect, color: Color) -> None:
    _unsupported("draw_unfilled_rectangle")


def draw_points(points: list[tuple[float, float]], color: Color) -> None:
    _unsupported("draw_points")


def draw_lines(points: list[tuple[float, float]], color: Color) -> None:
    _unsupported("draw_lines")


def draw_circle(
    center: tuple[float, float],
    radius: float,
    color: Color,
) -> None:
    _unsupported("draw_circle")


def draw_rectangle_rounded(
    rect: Rect,
    roundness: float,
    segments: int,
    color: Color,
) -> None:
    _unsupported("draw_rectangle_rounded")


def draw_rectangle_rounded_lines(
    rect: Rect,
    roundness: float,
    segments: int,
    color: Color,
) -> None:
    _unsupported("draw_rectangle_rounded_lines")


def draw_rectangle_lines_ex(
    rect: Rect,
    line_thickness: float,
    color: Color,
) -> None:
    _unsupported("draw_rectangle_lines_ex")


def draw_line_ex(
    start: tuple[float, float],
    end: tuple[float, float],
    thickness: float,
    color: Color,
) -> None:
    _unsupported("draw_line_ex")


def draw_text_ex(
    font: ArepyFont,
    text: str,
    position: tuple[float, float],
    font_size: float,
    spacing: float,
    color: Color,
) -> None:
    draw_text(text, position, int(font_size), color)


def screen_to_world(
    position: tuple[float, float],
    camera: object,
) -> tuple[float, float]:
    _unsupported("screen_to_world")


def add_camera(camera: object) -> None:
    _unsupported("add_camera")


def get_camera(id: int) -> object:
    _unsupported("get_camera")


def remove_camera(id: int) -> None:
    _unsupported("remove_camera")


def begin_camera_mode(camera: object) -> None:
    _unsupported("begin_camera_mode")


def end_camera_mode() -> None:
    _unsupported("end_camera_mode")


def update_camera(camera: object) -> None:
    _unsupported("update_camera")


def get_cameras() -> list[object]:
    _unsupported("get_cameras")


def get_current_camera() -> object:
    _unsupported("get_current_camera")


def disable_mouse_cursor() -> None:
    arepyRuntime.hideCursor()


def enable_mouse_cursor() -> None:
    arepyRuntime.showCursor()


def is_mouse_cursor_hidden() -> bool:
    return bool(arepyRuntime.cursorHidden())


def set_mouse_position(position: tuple[float, float]) -> None:
    _unsupported("set_mouse_position")


def begin_scissor_mode(x: int, y: int, width: int, height: int) -> None:
    arepyRuntime.beginClip(x, y, width, height)


def end_scissor_mode() -> None:
    arepyRuntime.endClip()


def draw_circle_lines(
    center: tuple[float, float],
    radius: float,
    color: Color,
) -> None:
    _unsupported("draw_circle_lines")


def draw_ellipse(
    center: tuple[float, float],
    radius_h: float,
    radius_v: float,
    color: Color,
) -> None:
    _unsupported("draw_ellipse")


def draw_ellipse_lines(
    center: tuple[float, float],
    radius_h: float,
    radius_v: float,
    color: Color,
) -> None:
    _unsupported("draw_ellipse_lines")


def draw_triangle(
    v1: tuple[float, float],
    v2: tuple[float, float],
    v3: tuple[float, float],
    color: Color,
) -> None:
    _unsupported("draw_triangle")


def draw_triangle_lines(
    v1: tuple[float, float],
    v2: tuple[float, float],
    v3: tuple[float, float],
    color: Color,
) -> None:
    _unsupported("draw_triangle_lines")


def draw_poly(
    center: tuple[float, float],
    sides: int,
    radius: float,
    rotation: float,
    color: Color,
) -> None:
    _unsupported("draw_poly")


def draw_poly_lines(
    center: tuple[float, float],
    sides: int,
    radius: float,
    rotation: float,
    color: Color,
) -> None:
    _unsupported("draw_poly_lines")


def draw_poly_lines_ex(
    center: tuple[float, float],
    sides: int,
    radius: float,
    rotation: float,
    line_thickness: float,
    color: Color,
) -> None:
    _unsupported("draw_poly_lines_ex")


def draw_ring(
    center: tuple[float, float],
    inner_radius: float,
    outer_radius: float,
    start_angle: float,
    end_angle: float,
    segments: int,
    color: Color,
) -> None:
    _unsupported("draw_ring")


def draw_ring_lines(
    center: tuple[float, float],
    inner_radius: float,
    outer_radius: float,
    start_angle: float,
    end_angle: float,
    segments: int,
    color: Color,
) -> None:
    _unsupported("draw_ring_lines")


def draw_line_bezier(
    start: tuple[float, float],
    end: tuple[float, float],
    thickness: float,
    color: Color,
) -> None:
    _unsupported("draw_line_bezier")


def draw_rectangle_gradient_v(
    rect: Rect,
    top_color: Color,
    bottom_color: Color,
) -> None:
    _unsupported("draw_rectangle_gradient_v")


def draw_rectangle_gradient_h(
    rect: Rect,
    left_color: Color,
    right_color: Color,
) -> None:
    _unsupported("draw_rectangle_gradient_h")


def draw_rectangle_gradient_ex(
    rect: Rect,
    top_left: Color,
    bottom_left: Color,
    top_right: Color,
    bottom_right: Color,
) -> None:
    _unsupported("draw_rectangle_gradient_ex")


def draw_pixel(position: tuple[float, float], color: Color) -> None:
    _unsupported("draw_pixel")


def init_stencil() -> bool:
    return False


def is_stencil_available() -> bool:
    return False


def begin_stencil_mask() -> None:
    _unsupported("begin_stencil_mask")


def end_stencil_mask() -> None:
    _unsupported("end_stencil_mask")


def end_stencil_mask_inverse() -> None:
    _unsupported("end_stencil_mask_inverse")


def end_stencil_mode() -> None:
    _unsupported("end_stencil_mode")


def init_streaming() -> bool:
    return False


def is_streaming_available() -> bool:
    return False


def create_streaming_texture(
    width: int,
    height: int,
    channels: int = 4,
) -> object:
    _unsupported("create_streaming_texture")


def update_streaming_texture(streaming: object, pixels: bytes) -> bool:
    _unsupported("update_streaming_texture")


def get_streaming_texture(streaming: object) -> ArepyTexture:
    _unsupported("get_streaming_texture")


def destroy_streaming_texture(streaming: object) -> None:
    _unsupported("destroy_streaming_texture")


def _unsupported(operation: str) -> None:
    raise NotImplementedError(
        f"Renderer2D.{operation} is not available in the current Arepy web backend."
    )


def _normalize_path(path: PathLike[str]) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


def _css_color(color: Color) -> str:
    return f"rgba({color.r},{color.g},{color.b},{color.a / 255})"
