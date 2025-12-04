"""
Streaming texture support using OpenGL PBO (Pixel Buffer Objects) via FFI.

This module provides high-performance texture streaming for video playback
and other dynamic texture updates using double-buffered PBOs for async
CPU to GPU pixel transfer.
"""

from raylib import ffi, rl
from typing import Optional
from dataclasses import dataclass, field

# OpenGL constants
GL_PIXEL_UNPACK_BUFFER = 0x88EC
GL_STREAM_DRAW = 0x88E0
GL_WRITE_ONLY = 0x88B9
GL_TEXTURE_2D = 0x0DE1
GL_RGBA = 0x1908
GL_RGB = 0x1907
GL_UNSIGNED_BYTE = 0x1401

# Function pointer cache
_gl_funcs: dict = {}
_initialized = False


def _get_gl_func(name: str, signature: str):
    """Get an OpenGL function pointer and cast it to the correct signature."""
    if name in _gl_funcs:
        return _gl_funcs[name]

    addr = rl.glfwGetProcAddress(name.encode("utf-8"))
    if addr == ffi.NULL:
        raise RuntimeError(f"Failed to get OpenGL function: {name}")

    func = ffi.cast(signature, addr)
    _gl_funcs[name] = func
    return func


def init_streaming() -> bool:
    """
    Initialize PBO streaming functions.
    Must be called after the OpenGL context is created.

    Returns:
        bool: True if initialization was successful.
    """
    global _initialized
    if _initialized:
        return True

    try:
        _get_gl_func("glGenBuffers", "void(*)(int, unsigned int*)")
        _get_gl_func("glDeleteBuffers", "void(*)(int, unsigned int*)")
        _get_gl_func("glBindBuffer", "void(*)(unsigned int, unsigned int)")
        _get_gl_func("glBufferData", "void(*)(unsigned int, long long, void*, unsigned int)")
        _get_gl_func("glMapBuffer", "void*(*)(unsigned int, unsigned int)")
        _get_gl_func("glUnmapBuffer", "unsigned char(*)(unsigned int)")
        _get_gl_func("glBindTexture", "void(*)(unsigned int, unsigned int)")
        _get_gl_func("glTexSubImage2D", "void(*)(unsigned int, int, int, int, int, int, unsigned int, unsigned int, void*)")

        _initialized = True
        return True
    except RuntimeError as e:
        print(f"PBO streaming init failed: {e}")
        return False


def is_streaming_available() -> bool:
    """Check if PBO streaming is initialized and available."""
    return _initialized


@dataclass
class StreamingTexture:
    """
    A texture with double-buffered PBO for async streaming updates.
    """
    texture_id: int
    width: int
    height: int
    channels: int  # 3 for RGB, 4 for RGBA
    _pbo_ids: list = field(default_factory=list)  # Two PBOs for double buffering
    _current_pbo: int = 0  # Index of current PBO (0 or 1)
    _buffer_size: int = 0
    _arepy_texture: Optional[object] = None  # Reference to ArepyTexture

    def __post_init__(self):
        self._buffer_size = self.width * self.height * self.channels


def create_streaming_texture(width: int, height: int, channels: int = 4) -> Optional[StreamingTexture]:
    """
    Create a streaming texture with double-buffered PBOs.

    Args:
        width: Texture width in pixels.
        height: Texture height in pixels.
        channels: Number of color channels (3 for RGB, 4 for RGBA).

    Returns:
        StreamingTexture object or None if failed.
    """
    if not _initialized:
        if not init_streaming():
            return None

    # Flush any pending raylib draws
    rl.rlDrawRenderBatchActive()

    glGenBuffers = _gl_funcs["glGenBuffers"]
    glBindBuffer = _gl_funcs["glBindBuffer"]
    glBufferData = _gl_funcs["glBufferData"]

    # Create an empty raylib texture
    format_type = rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 if channels == 4 else rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8
    
    # Generate empty image and create texture
    image = rl.GenImageColor(width, height, (0, 0, 0, 255))
    texture = rl.LoadTextureFromImage(image)
    rl.UnloadImage(image)

    if texture.id == 0:
        print("Failed to create texture for streaming")
        return None

    # Create two PBOs for double buffering
    buffer_size = width * height * channels
    pbo_ids = ffi.new("unsigned int[2]")
    glGenBuffers(2, pbo_ids)

    # Initialize both PBOs with empty data
    for i in range(2):
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo_ids[i])
        glBufferData(GL_PIXEL_UNPACK_BUFFER, buffer_size, ffi.NULL, GL_STREAM_DRAW)

    # Unbind PBO
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)

    # Create ArepyTexture wrapper
    from arepy.engine.renderer import ArepyTexture
    arepy_texture = ArepyTexture(texture.id, (width, height))
    arepy_texture._ref_texture = texture

    streaming = StreamingTexture(
        texture_id=texture.id,
        width=width,
        height=height,
        channels=channels,
        _pbo_ids=[pbo_ids[0], pbo_ids[1]],
        _current_pbo=0,
        _buffer_size=buffer_size,
        _arepy_texture=arepy_texture,
    )

    return streaming


def update_streaming_texture(streaming: StreamingTexture, pixels: bytes) -> bool:
    """
    Update a streaming texture with new pixel data using PBO double buffering.

    This function uses async transfer - it uploads the previous frame's data
    while you write new data, minimizing GPU stalls.

    Args:
        streaming: The StreamingTexture to update.
        pixels: Raw pixel data (RGB or RGBA bytes, must match texture size).

    Returns:
        bool: True if update was successful.
    """
    if not _initialized or streaming is None:
        return False

    if len(pixels) != streaming._buffer_size:
        print(f"Pixel data size mismatch: expected {streaming._buffer_size}, got {len(pixels)}")
        return False

    # Flush any pending raylib draws
    rl.rlDrawRenderBatchActive()

    glBindBuffer = _gl_funcs["glBindBuffer"]
    glBufferData = _gl_funcs["glBufferData"]
    glMapBuffer = _gl_funcs["glMapBuffer"]
    glUnmapBuffer = _gl_funcs["glUnmapBuffer"]
    glBindTexture = _gl_funcs["glBindTexture"]
    glTexSubImage2D = _gl_funcs["glTexSubImage2D"]

    # Index of PBO to update texture from (previous frame's data)
    next_pbo = 1 - streaming._current_pbo
    current_pbo = streaming._current_pbo

    # Bind texture
    glBindTexture(GL_TEXTURE_2D, streaming.texture_id)

    # Bind PBO that has the previous frame's data and update texture
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER, streaming._pbo_ids[next_pbo])

    # Update texture from PBO (async, doesn't wait for transfer)
    gl_format = GL_RGBA if streaming.channels == 4 else GL_RGB
    glTexSubImage2D(
        GL_TEXTURE_2D,
        0,  # mipmap level
        0, 0,  # x, y offset
        streaming.width, streaming.height,
        gl_format,
        GL_UNSIGNED_BYTE,
        ffi.NULL  # Read from bound PBO at offset 0
    )

    # Now bind the other PBO to write new data
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER, streaming._pbo_ids[current_pbo])

    # Orphan the buffer (allocate new storage, old data can be transferred async)
    glBufferData(GL_PIXEL_UNPACK_BUFFER, streaming._buffer_size, ffi.NULL, GL_STREAM_DRAW)

    # Map buffer to write pixels
    ptr = glMapBuffer(GL_PIXEL_UNPACK_BUFFER, GL_WRITE_ONLY)
    if ptr == ffi.NULL:
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
        return False

    # Copy pixels to PBO
    ffi.memmove(ptr, pixels, streaming._buffer_size)

    # Unmap buffer
    glUnmapBuffer(GL_PIXEL_UNPACK_BUFFER)

    # Unbind PBO
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)

    # Swap PBO index for next frame
    streaming._current_pbo = next_pbo

    return True


def get_texture(streaming: StreamingTexture):
    """
    Get the ArepyTexture for drawing.

    Args:
        streaming: The StreamingTexture.

    Returns:
        ArepyTexture that can be used with renderer.draw_texture().
    """
    return streaming._arepy_texture


def destroy_streaming_texture(streaming: StreamingTexture) -> None:
    """
    Clean up streaming texture resources.

    Args:
        streaming: The StreamingTexture to destroy.
    """
    if not _initialized or streaming is None:
        return

    glDeleteBuffers = _gl_funcs["glDeleteBuffers"]

    # Delete PBOs
    pbo_ids = ffi.new("unsigned int[2]", streaming._pbo_ids)
    glDeleteBuffers(2, pbo_ids)

    # Unload raylib texture
    if streaming._arepy_texture and streaming._arepy_texture._ref_texture:
        rl.UnloadTexture(streaming._arepy_texture._ref_texture)
