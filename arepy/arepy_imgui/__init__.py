from typing import cast

from .imgui_repository import ImguiRendererRepository, ImGuiRepository

try:
    import imgui
    from imgui.integrations.sdl2 import SDL2Renderer

    imgui = cast(ImGuiRepository, imgui)
    ImguiRenderer = cast(ImguiRendererRepository, SDL2Renderer)
except ImportError:

    class Default:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return self

        def __call__(self, *args, **kwargs):
            return self

    none_impl = Default()
    imgui = cast(ImGuiRepository, none_impl)
    ImguiRenderer = cast(ImguiRendererRepository, none_impl)
