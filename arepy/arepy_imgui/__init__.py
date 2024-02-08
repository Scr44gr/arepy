from typing import cast

from .imgui_repository import ImGuiRepository

try:
    import imgui

    imgui = cast(ImGuiRepository, imgui)
except ImportError:
    imgui = cast(ImGuiRepository, None)
