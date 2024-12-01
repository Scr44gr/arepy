from typing import Any, Dict, Type

from ..asset_store import AssetStore
from ..builders import EntityBuilder
from ..ecs.registry import Registry
from ..ecs.systems import System, SystemPipeline
from ..event_manager import EventManager
from .display import DisplayRepository
from .input import InputRepository
from .renderer.renderer_2d import Color, Renderer2D

Resources: Dict[str, Any] = {}


class ArepyEngine:
    title: str = "Arepy Engine"
    window_width: int = 640
    window_height: int = 480
    # Logical size
    render_size = (window_width, window_height)
    max_frame_rate: int = 60
    debug: bool = False
    fullscreen: bool = False
    fake_fullscreen: bool = False
    vsync: bool = False

    def __init__(self):
        from ..container import dependencies

        self._asset_store = AssetStore()
        self._event_manager = EventManager()
        self.display = dependencies().display_repository
        self.renderer = dependencies().renderer_repository
        self.input = dependencies().input_repository
        # add resources
        Resources[DisplayRepository.__name__] = self.display
        Resources[Renderer2D.__name__] = self.renderer
        Resources[InputRepository.__name__] = self.input
        Resources[EventManager.__name__] = self._event_manager
        Resources[AssetStore.__name__] = self._asset_store

        self._registry = Registry()
        self._registry.resources = Resources

    def init(self):
        self.display.set_vsync(self.vsync)
        self.display.create_window(self.window_width, self.window_height, self.title)
        self.renderer.set_max_framerate(self.max_frame_rate)
        if self.fullscreen:
            self.display.toggle_fullscreen()

    def run(self):

        self.on_startup()
        while not self.display.window_should_close():
            self.__input_process()
            self.__update_process()
            self.__render_process()

        self.on_shutdown()

    def __input_process(self): ...

    def __update_process(self):
        self._registry.run(pipeline=SystemPipeline.UPDATE)
        self.on_update()
        self._registry.update()

    def __render_process(self):
        self.renderer.start_frame()
        self.renderer.clear(color=Color(245, 245, 245, 255))
        self._registry.run(pipeline=SystemPipeline.RENDER)
        self.on_render()
        self.renderer.draw_fps(position=(10, 10))
        self.renderer.end_frame()

    def create_entity(self) -> EntityBuilder:
        """Create an entity builder.

        Returns:
            An entity builder.
        """
        entity = self._registry.create_entity()
        return EntityBuilder(entity, self._registry)

    def add_system(self, pipeline: SystemPipeline, system: System) -> None:
        """Create a new system.

        Args:
            pipeline: A pipeline to add the system.
            system: A system.
        """
        self._registry.add_system(pipeline, system)

    def get_asset_store(self) -> AssetStore:
        """Get the asset store.

        Returns:
            The asset store.
        """
        return self._asset_store

    def get_event_manager(self) -> EventManager:
        """Get the event manager.

        Returns:
            The event manager.
        """
        return self._event_manager

    # Engine func Events
    def on_startup(self): ...
    def on_update(self): ...
    def on_shutdown(self): ...
    def on_render(self): ...
