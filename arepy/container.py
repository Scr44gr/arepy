# dependency injection container
from dataclasses import dataclass
from typing import Callable, cast

from .arepy_imgui.imgui_repository import Default as EmptyRepository
from .arepy_imgui.imgui_repository import ImGui, ImGuiRendererRepository
from .engine.display import Display
from .engine.input import Input
from .engine.integrations.raylib.display import display_repository

# ModernGLRenderer implementation
from .engine.integrations.raylib.input import input_repository
from .engine.integrations.raylib.renderer import renderer_2d
from .engine.renderer.renderer_2d import Renderer2D

try:
    from imgui_bundle import imgui, imgui_ctx

    from .engine.integrations.imgui.backend import ImguiBackend

    imgui.create_context()
except (ImportError, ModuleNotFoundError):
    imgui = None
    imgui_ctx = None
    ImguiRenderer = EmptyRepository


@dataclass(frozen=True)
class Dependencies:
    """Dependency container for the application."""

    input_repository: Input
    imgui_repository: ImGui
    display_repository: Display
    renderer_repository: Renderer2D
    imgui_renderer_repository: Callable[..., ImGuiRendererRepository]


def _build_dependencies() -> Callable[[], Dependencies]:
    """Build the dependency container."""

    deps = Dependencies(
        display_repository=cast(Display, display_repository),
        renderer_repository=cast(Renderer2D, renderer_2d),
        # imgui backend renderer
        imgui_renderer_repository=(
            cast(
                Callable[..., ImGuiRendererRepository],
                ImguiBackend if imgui is not None else EmptyRepository,
            )
        ),
        input_repository=cast(Input, input_repository),
        # for gui manipulation
        imgui_repository=(
            cast(ImGui, imgui if imgui is not None else EmptyRepository())
        ),
    )

    def fn() -> Dependencies:
        return deps

    return fn


dependencies = _build_dependencies()
