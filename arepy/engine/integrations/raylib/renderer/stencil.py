"""
Stencil buffer support using OpenGL functions via FFI.

This module provides stencil masking functionality by directly calling
OpenGL functions through raylib's FFI interface.
"""

from raylib import ffi, rl
from typing import Optional

# OpenGL constants
GL_STENCIL_TEST = 0x0B90
GL_STENCIL_BUFFER_BIT = 0x00000400
GL_ALWAYS = 0x0207
GL_KEEP = 0x1E00
GL_REPLACE = 0x1E01
GL_EQUAL = 0x0202
GL_NOTEQUAL = 0x0205

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


def init_stencil() -> bool:
    """
    Initialize stencil buffer functions.
    Must be called after the OpenGL context is created (after engine.run() starts).

    Returns:
        bool: True if initialization was successful.
    """
    global _initialized
    if _initialized:
        return True

    try:
        # Load all required OpenGL functions
        _get_gl_func("glEnable", "void(*)(unsigned int)")
        _get_gl_func("glDisable", "void(*)(unsigned int)")
        _get_gl_func("glClear", "void(*)(unsigned int)")
        _get_gl_func("glStencilFunc", "void(*)(unsigned int, int, unsigned int)")
        _get_gl_func("glStencilOp", "void(*)(unsigned int, unsigned int, unsigned int)")
        _get_gl_func("glStencilMask", "void(*)(unsigned int)")
        _get_gl_func("glColorMask", "void(*)(unsigned char, unsigned char, unsigned char, unsigned char)")

        _initialized = True
        return True
    except RuntimeError as e:
        print(f"Stencil init failed: {e}")
        return False


def begin_stencil_mask() -> None:
    """
    Begin defining a stencil mask.
    Draw shapes after this call to define the mask area.
    The shapes drawn will not be visible - only the mask is written.
    """
    if not _initialized:
        if not init_stencil():
            return

    # Flush any pending raylib draws
    rl.rlDrawRenderBatchActive()

    glEnable = _gl_funcs["glEnable"]
    glStencilFunc = _gl_funcs["glStencilFunc"]
    glStencilOp = _gl_funcs["glStencilOp"]
    glStencilMask = _gl_funcs["glStencilMask"]
    glColorMask = _gl_funcs["glColorMask"]
    glClear = _gl_funcs["glClear"]

    # Enable stencil test
    glEnable(GL_STENCIL_TEST)

    # Clear stencil buffer
    glStencilMask(0xFF)
    glClear(GL_STENCIL_BUFFER_BIT)

    # Configure stencil to write 1 where we draw
    glStencilFunc(GL_ALWAYS, 1, 0xFF)
    glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
    glStencilMask(0xFF)

    # Disable color writing - we only want to write to stencil buffer
    glColorMask(0, 0, 0, 0)


def end_stencil_mask() -> None:
    """
    End defining the stencil mask.
    After this call, subsequent draws will only appear where the mask was drawn.
    """
    if not _initialized:
        return

    # Flush the mask draws
    rl.rlDrawRenderBatchActive()

    glStencilFunc = _gl_funcs["glStencilFunc"]
    glStencilOp = _gl_funcs["glStencilOp"]
    glStencilMask = _gl_funcs["glStencilMask"]
    glColorMask = _gl_funcs["glColorMask"]

    # Re-enable color writing
    glColorMask(1, 1, 1, 1)

    # Configure stencil to only draw where stencil value is 1
    glStencilFunc(GL_EQUAL, 1, 0xFF)
    glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
    glStencilMask(0x00)  # Don't write to stencil buffer anymore


def end_stencil_mask_inverse() -> None:
    """
    End defining the stencil mask with inverse mode.
    After this call, subsequent draws will only appear where the mask was NOT drawn.
    """
    if not _initialized:
        return

    # Flush the mask draws
    rl.rlDrawRenderBatchActive()

    glStencilFunc = _gl_funcs["glStencilFunc"]
    glStencilOp = _gl_funcs["glStencilOp"]
    glStencilMask = _gl_funcs["glStencilMask"]
    glColorMask = _gl_funcs["glColorMask"]

    # Re-enable color writing
    glColorMask(1, 1, 1, 1)

    # Configure stencil to only draw where stencil value is NOT 1
    glStencilFunc(GL_NOTEQUAL, 1, 0xFF)
    glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
    glStencilMask(0x00)


def end_stencil_mode() -> None:
    """
    Disable stencil testing and return to normal rendering.
    Call this after you're done drawing masked content.
    """
    if not _initialized:
        return

    # Flush any pending draws
    rl.rlDrawRenderBatchActive()

    glDisable = _gl_funcs["glDisable"]
    glStencilMask = _gl_funcs["glStencilMask"]

    # Disable stencil test
    glDisable(GL_STENCIL_TEST)
    glStencilMask(0xFF)


def is_stencil_available() -> bool:
    """
    Check if stencil buffer is initialized and available.

    Returns:
        bool: True if stencil is available.
    """
    return _initialized


# Aliases for convenience
clear_stencil = end_stencil_mode
