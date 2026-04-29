from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from imgui_bundle import imgui as imgui
    from imgui_bundle import imgui_ctx as imgui_ctx
else:
    try:
        from imgui_bundle import imgui, imgui_ctx
    except (ImportError, ModuleNotFoundError):
        imgui = None
        imgui_ctx = None


def is_available() -> bool:
    return imgui is not None


__all__ = ["imgui", "imgui_ctx", "is_available"]
