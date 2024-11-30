# dependency injection container
from dataclasses import dataclass
from typing import Callable, cast

from .engine.display import DisplayRepository
from .engine.input import InputRepository
from .engine.integrations.raylib.display import display_repository
from .engine.integrations.raylib.input import input_repository
from .engine.integrations.raylib.renderer import renderer_2d
from .engine.renderer.renderer_2d import Renderer2D


@dataclass(frozen=True)
class Dependencies:
    """Dependency container for the application."""

    display_repository: DisplayRepository
    renderer_repository: Renderer2D
    input_repository: InputRepository


def _build_dependencies() -> Callable[[], Dependencies]:
    """Build the dependency container."""

    deps = Dependencies(
        display_repository=cast(DisplayRepository, display_repository),
        renderer_repository=cast(Renderer2D, renderer_2d),
        input_repository=cast(InputRepository, input_repository),
    )

    def fn() -> Dependencies:
        return deps

    return fn


dependencies = _build_dependencies()
