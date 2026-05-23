"""Public 2D rendering protocol and helper value objects."""

from os import PathLike
from typing import Optional, Protocol

import numpy as np
from numpy.typing import NDArray

from ...bundle.components.camera import Camera2D
from . import (
    ArepyFont,
    ArepyShader,
    ArepyTexture,
    Color,
    Rect,
    ShaderUniformType,
    ShaderValue,
    TextureFilter,
)
from .texture_atlas import TextureAtlasCollection, TextureBatchLayout

FloatBatchView = NDArray[np.float64]


class Renderer2D(Protocol):
    """Protocol defining the public 2D renderer interface.

    The engine registers one `Renderer2D` implementation as a shared resource,
    so gameplay systems can receive it through type-based injection.
    """

    # Texture methods
    def create_render_texture(self, width: int, height: int) -> ArepyTexture:
        """Create an off-screen texture you can render into."""
        ...

    def create_texture(self, path: PathLike[str]) -> ArepyTexture:
        """Load a texture from an image file path."""
        ...

    def unload_texture(self, texture: ArepyTexture) -> None:
        """Release a texture when you no longer need it."""
        ...

    # Shader methods
    def load_shader(
        self,
        vertex_path: Optional[PathLike[str]] = None,
        fragment_path: Optional[PathLike[str]] = None,
    ) -> ArepyShader:
        """Load a shader from files on disk. At least one stage must be provided."""
        ...

    def compile_shader(
        self,
        vertex_source: Optional[str] = None,
        fragment_source: Optional[str] = None,
    ) -> ArepyShader:
        """Compile a shader from in-memory GLSL source strings."""
        ...

    def unload_shader(self, shader: ArepyShader) -> None:
        """Release a shader when you no longer need it."""
        ...

    def begin_shader_mode(self, shader: ArepyShader) -> None:
        """Route subsequent draw calls through the given shader."""
        ...

    def end_shader_mode(self) -> None:
        """Stop using the current shader."""
        ...

    def set_shader_value(
        self,
        shader: ArepyShader,
        uniform_type: ShaderUniformType,
        name: str,
        value: ShaderValue,
    ) -> None:
        """Set a shader uniform by name, caching the backend location internally."""
        ...

    # Draw methods
    def bind_render_texture(self, texture: ArepyTexture) -> None:
        """Start drawing into a render texture instead of the window backbuffer."""
        ...

    def unbind_render_texture(self) -> None:
        """Stop drawing into the current render texture and return to the backbuffer."""
        ...

    def draw_texture(
        self, texture: ArepyTexture, source: Rect, dest: Rect, color: Color
    ) -> None:
        """Draw a texture region into a destination rectangle with tinting."""
        ...

    def draw_texture_ex(
        self,
        texture: ArepyTexture,
        source: Rect,
        dest: Rect,
        origin: tuple[float, float],
        rotation: float,
        color: Color,
    ) -> None:
        """Draw a texture with origin and rotation control."""
        ...

    def draw_texture_batch(
        self,
        atlases: TextureAtlasCollection,
        layout: TextureBatchLayout,
        position_x: FloatBatchView,
        position_y: FloatBatchView,
        color: Color,
    ) -> None:
        """Draw a precomputed atlas-backed sprite batch using NumPy position views."""
        ...

    def draw_rectangle(self, rect: Rect, color: Color) -> None:
        """Draw a filled rectangle."""
        ...

    def draw_rectangle_ex(self, rect: Rect, rotation: float, color: Color) -> None:
        """Draw a filled rectangle with rotation applied."""
        ...

    def draw_unfilled_rectangle(self, rect: Rect, color: Color) -> None:
        """Draw only the outline of a rectangle."""
        ...

    def draw_points(self, points: list[tuple[float, float]], color: Color) -> None:
        """Draw a collection of points."""
        ...

    def draw_lines(self, points: list[tuple[float, float]], color: Color) -> None:
        """Draw connected line segments through a list of points."""
        ...

    def draw_circle(
        self, center: tuple[float, float], radius: float, color: Color
    ) -> None:
        """Draw a filled circle."""
        ...

    def draw_rectangle_rounded(
        self, rect: Rect, roundness: float, segments: int, color: Color
    ) -> None: ...
    def draw_rectangle_rounded_lines(
        self, rect: Rect, roundness: float, segments: int, color: Color
    ) -> None: ...
    def draw_rectangle_lines_ex(
        self, rect: Rect, line_thickness: float, color: Color
    ) -> None: ...
    def draw_line_ex(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        thickness: float,
        color: Color,
    ) -> None:
        """Draw a thick line between two points."""
        ...

    def draw_text(
        self, text: str, position: tuple[float, float], font_size: int, color: Color
    ) -> None:
        """Draw text with the default font."""
        ...

    def draw_text_ex(
        self,
        font: ArepyFont,
        text: str,
        position: tuple[float, float],
        font_size: float,
        spacing: float,
        color: Color,
    ) -> None:
        """Draw text with an explicit font, size, and spacing."""
        ...

    def draw_fps(
        self,
        position: tuple[int, int],
    ) -> None:
        """Draw the current frames-per-second counter on screen."""
        ...

    def measure_text(self, text: str, font_size: int) -> int:
        """Return the width in pixels of text rendered with the default font."""
        ...

    def measure_text_ex(
        self, font: ArepyFont, text: str, font_size: float, spacing: float
    ) -> tuple[float, float]:
        """Return the width and height of text rendered with a specific font."""
        ...

    def screen_to_world(
        self, position: tuple[float, float], camera: Camera2D
    ) -> tuple[float, float]:
        """Convert screen coordinates into world coordinates using a camera."""
        ...

    # Frame methods
    def set_texture_filter(self, texture: ArepyTexture, filter: TextureFilter) -> None:
        """Set the sampling filter used when a texture is scaled."""
        ...

    def set_max_framerate(self, max_frame_rate: int) -> None:
        """Set the upper frame-rate limit used by the renderer."""
        ...

    def clear(self, color: Color) -> None:
        """Clear the active render target with a solid color."""
        ...

    def start_frame(self) -> None:
        """Begin a new frame on the active render target."""
        ...

    def end_frame(self) -> None:
        """Finish issuing draw commands for the current frame."""
        ...

    def flush(self) -> None:
        """Force pending draw commands to be submitted."""
        ...

    def swap_buffers(self) -> None:
        """Present the finished frame to the window."""
        ...

    def get_delta_time(self) -> float:
        """Return the elapsed time in seconds since the previous frame."""
        ...

    def get_framerate(self) -> int:
        """Return the current measured frames per second."""
        ...

    # Camera methods
    def add_camera(self, camera: Camera2D) -> None:
        """Register a 2D camera so it can be reused later."""
        ...

    def get_camera(self, id: int) -> Optional[Camera2D]: ...
    def remove_camera(self, id: int) -> None: ...
    def begin_camera_mode(self, camera: Camera2D) -> None:
        """Start drawing using the given camera transform."""
        ...

    def end_camera_mode(self) -> None:
        """Stop drawing through the current camera."""
        ...

    def update_camera(self, camera: Camera2D) -> None:
        """Apply backend-specific updates to a camera before or during use."""
        ...

    def get_cameras(self) -> list[Camera2D]: ...
    def get_current_camera(self) -> Camera2D: ...
    def disable_mouse_cursor(self) -> None: ...
    def enable_mouse_cursor(self) -> None: ...
    def is_mouse_cursor_hidden(self) -> bool: ...
    def set_mouse_position(self, position: tuple[float, float]) -> None: ...

    def begin_scissor_mode(self, x: int, y: int, width: int, height: int) -> None:
        """Clip subsequent drawing to a rectangular screen region."""
        ...

    def end_scissor_mode(self) -> None: ...

    def load_font_ex(
        self,
        path: PathLike[str],
        base_size: int,
        codepoints: Optional[list[int]],
        count: int,
    ) -> ArepyFont:
        """Load a font from disk with a chosen base size and codepoint set."""
        ...

    def get_font_default(self) -> ArepyFont:
        """Return the backend's default font."""
        ...

    def unload_font(self, font: ArepyFont) -> None:
        """Release a previously loaded font."""
        ...

    # Additional shape drawing methods
    def draw_circle_lines(
        self, center: tuple[float, float], radius: float, color: Color
    ) -> None: ...
    def draw_ellipse(
        self,
        center: tuple[float, float],
        radius_h: float,
        radius_v: float,
        color: Color,
    ) -> None: ...
    def draw_ellipse_lines(
        self,
        center: tuple[float, float],
        radius_h: float,
        radius_v: float,
        color: Color,
    ) -> None: ...
    def draw_triangle(
        self,
        v1: tuple[float, float],
        v2: tuple[float, float],
        v3: tuple[float, float],
        color: Color,
    ) -> None: ...
    def draw_triangle_lines(
        self,
        v1: tuple[float, float],
        v2: tuple[float, float],
        v3: tuple[float, float],
        color: Color,
    ) -> None: ...
    def draw_poly(
        self,
        center: tuple[float, float],
        sides: int,
        radius: float,
        rotation: float,
        color: Color,
    ) -> None: ...
    def draw_poly_lines(
        self,
        center: tuple[float, float],
        sides: int,
        radius: float,
        rotation: float,
        color: Color,
    ) -> None: ...
    def draw_poly_lines_ex(
        self,
        center: tuple[float, float],
        sides: int,
        radius: float,
        rotation: float,
        line_thickness: float,
        color: Color,
    ) -> None: ...
    def draw_ring(
        self,
        center: tuple[float, float],
        inner_radius: float,
        outer_radius: float,
        start_angle: float,
        end_angle: float,
        segments: int,
        color: Color,
    ) -> None: ...
    def draw_ring_lines(
        self,
        center: tuple[float, float],
        inner_radius: float,
        outer_radius: float,
        start_angle: float,
        end_angle: float,
        segments: int,
        color: Color,
    ) -> None: ...
    def draw_line_bezier(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        thickness: float,
        color: Color,
    ) -> None: ...
    def draw_rectangle_gradient_v(
        self, rect: Rect, top_color: Color, bottom_color: Color
    ) -> None: ...
    def draw_rectangle_gradient_h(
        self, rect: Rect, left_color: Color, right_color: Color
    ) -> None: ...
    def draw_rectangle_gradient_ex(
        self,
        rect: Rect,
        top_left: Color,
        bottom_left: Color,
        top_right: Color,
        bottom_right: Color,
    ) -> None: ...
    def draw_pixel(self, position: tuple[float, float], color: Color) -> None: ...

    # Stencil mask methods
    def init_stencil(self) -> bool:
        """Initialize stencil support if the backend provides it."""
        ...

    def is_stencil_available(self) -> bool:
        """Return whether stencil operations are currently supported."""
        ...

    def begin_stencil_mask(self) -> None:
        """Start writing a stencil mask from subsequent draw calls."""
        ...

    def end_stencil_mask(self) -> None:
        """Finish the mask and begin drawing only inside the masked region."""
        ...

    def end_stencil_mask_inverse(self) -> None: ...
    def end_stencil_mode(self) -> None: ...

    # Streaming texture methods (PBO-based for video/dynamic content)
    def init_streaming(self) -> bool:
        """Initialize backend support for dynamic streaming textures."""
        ...

    def is_streaming_available(self) -> bool:
        """Return whether streaming texture support is available."""
        ...

    def create_streaming_texture(
        self, width: int, height: int, channels: int = 4
    ) -> object:
        """Create a texture handle optimized for frequent pixel uploads."""
        ...

    def update_streaming_texture(self, streaming: object, pixels: bytes) -> bool:
        """Upload a new pixel buffer into a streaming texture."""
        ...

    def get_streaming_texture(self, streaming: object) -> ArepyTexture:
        """Return the drawable texture associated with a streaming handle."""
        ...

    def destroy_streaming_texture(self, streaming: object) -> None:
        """Release a streaming texture and its backend resources."""
        ...
