# dependency injection container
from dataclasses import dataclass
from typing import Callable, cast

from .arepy_imgui.imgui_repository import Default as EmptyRepository
from .arepy_imgui.imgui_repository import Imgui, ImGuiRendererRepository
from .engine.audio import AudioDevice
from .engine.display import Display
from .engine.input import Input
from .engine.integrations.raylib.audio import audio_device
from .engine.integrations.raylib.display import display_repository
from .engine.integrations.raylib.input import input_repository
from .engine.integrations.raylib.renderer import renderer_2d, renderer_3d
from .engine.renderer.renderer_2d import Renderer2D
from .engine.renderer.renderer_3d import Renderer3D

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

    audio_device_repository: AudioDevice
    input_repository: Input
    imgui_repository: Imgui
    display_repository: Display
    renderer_repository: Renderer2D
    renderer_3d_repository: Renderer3D
    imgui_renderer_repository: Callable[..., ImGuiRendererRepository]


def _build_dependencies() -> Callable[[], Dependencies]:
    """Build the dependency container."""

    deps = Dependencies(
        display_repository=cast(Display, display_repository),
        renderer_repository=cast(Renderer2D, renderer_2d),
        renderer_3d_repository=cast(Renderer3D, renderer_3d),
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
            cast(Imgui, imgui if imgui is not None else EmptyRepository())
        ),
        audio_device_repository=cast(AudioDevice, audio_device),
    )

    def fn() -> Dependencies:
        return deps

    return fn


dependencies = _build_dependencies()
