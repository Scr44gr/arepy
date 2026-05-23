from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Protocol, cast

import numpy as np
from numpy.typing import NDArray
from raylib import ffi, rl

from arepy.engine.renderer import ArepyTexture, Color
from arepy.engine.renderer.texture_atlas import TextureBatchGroup

_native_module: Any | None = None
_native_checked = False
_render_backend_configured = False
_draw_texture_batch: Callable[..., None] | None = None


class _TextureRef(Protocol):
    id: int
    width: int
    height: int
    mipmaps: int
    format: int


def _load_native_module() -> Any | None:
    global _native_module, _native_checked
    if _native_checked:
        return _native_module

    _native_checked = True
    try:
        _native_module = import_module("arepy_renderer")
    except ImportError:
        _native_module = None
    return _native_module


def _configure_render_backend(module: Any) -> None:
    global _render_backend_configured
    if _render_backend_configured:
        return

    module.configure_render_backend(
        int(ffi.cast("uintptr_t", ffi.addressof(rl, "DrawTextureRec"))),
        int(ffi.cast("uintptr_t", ffi.addressof(rl, "rlDrawRenderBatchActive"))),
    )
    _render_backend_configured = True


def _initialize_native_backend() -> None:
    global _draw_texture_batch
    module = _load_native_module()
    if module is None:
        return

    _configure_render_backend(module)
    _draw_texture_batch = cast(Callable[..., None], module.draw_texture_batch)


_initialize_native_backend()


def is_available() -> bool:
    return _draw_texture_batch is not None


def draw_texture_batch_group(
    group: TextureBatchGroup,
    position_x: NDArray[np.float64],
    position_y: NDArray[np.float64],
    color: Color,
) -> bool:
    draw_texture_batch = _draw_texture_batch
    if draw_texture_batch is None:
        return False

    texture_ref = _require_texture_ref(group.texture)
    draw_texture_batch(
        int(texture_ref.id),
        int(texture_ref.width),
        int(texture_ref.height),
        int(texture_ref.mipmaps),
        int(texture_ref.format),
        _as_int64_array(group.entity_indices),
        _as_float32_array(group.source_x),
        _as_float32_array(group.source_y),
        _as_float32_array(group.source_width),
        _as_float32_array(group.source_height),
        _as_float64_array(position_x),
        _as_float64_array(position_y),
        (color.r, color.g, color.b, color.a),
    )
    return True


def _require_texture_ref(texture: ArepyTexture) -> _TextureRef:
    if texture._ref_texture is None:
        raise RuntimeError(
            "draw_texture_batch requires an ArepyTexture with a live raylib texture reference."
        )
    return cast(_TextureRef, texture._ref_texture)


def _as_int64_array(values: NDArray[np.int64]) -> NDArray[np.int64]:
    return np.require(values, dtype=np.int64, requirements=("C", "ALIGNED"))


def _as_float32_array(values: NDArray[np.float32]) -> NDArray[np.float32]:
    return np.require(values, dtype=np.float32, requirements=("C", "ALIGNED"))


def _as_float64_array(values: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.require(values, dtype=np.float64, requirements=("C", "ALIGNED"))
