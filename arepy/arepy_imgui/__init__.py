from typing import cast

from .imgui_repository import Default, ImguiRendererRepository, ImGuiRepository

try:
    import imgui
    from imgui.integrations.sdl2 import SDL2Renderer

    imgui = cast(ImGuiRepository, imgui)
    ImguiRenderer = cast(ImguiRendererRepository, SDL2Renderer)
except ImportError:

    none_impl = Default()
    imgui = cast(ImGuiRepository, none_impl)
    ImguiRenderer = cast(ImguiRendererRepository, none_impl)
