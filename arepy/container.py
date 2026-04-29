# dependency injection container
from dataclasses import dataclass
from typing import Any, Callable

from .arepy_imgui import imgui as bundled_imgui
from .engine.audio import AudioDevice
from .engine.display import Display
from .engine.input import Input
from .engine.integrations.raylib.audio import audio_device
from .engine.integrations.raylib.display import display_repository
from .engine.integrations.raylib.input import input_repository
from .engine.integrations.raylib.renderer import renderer_2d, renderer_3d
from .engine.renderer.renderer_2d import Renderer2D
from .engine.renderer.renderer_3d import Renderer3D

imgui_module = bundled_imgui
imgui_backend_factory: Callable[[], Any] | None = None

if imgui_module is not None:
    try:
        from .engine.integrations.imgui.backend import ImguiBackend
    except (ImportError, ModuleNotFoundError):
        imgui_module = None
    else:
        imgui_module.create_context()
        imgui_backend_factory = ImguiBackend


@dataclass(frozen=True)
class Dependencies:
    """Dependency container for the application."""

    audio_device_repository: AudioDevice
    input_repository: Input
    imgui_module: Any | None
    display_repository: Display
    renderer_repository: Renderer2D
    renderer_3d_repository: Renderer3D
    imgui_backend_factory: Callable[[], Any] | None


def _build_dependencies() -> Callable[[], Dependencies]:
    """Build the dependency container."""

    deps = Dependencies(
        display_repository=display_repository,
        renderer_repository=renderer_2d,
        renderer_3d_repository=renderer_3d,
        imgui_backend_factory=imgui_backend_factory,
        input_repository=input_repository,
        imgui_module=imgui_module,
        audio_device_repository=audio_device,
    )

    def fn() -> Dependencies:
        return deps

    return fn


dependencies = _build_dependencies()
