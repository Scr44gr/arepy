from threading import Thread
from typing import Any, Dict, Type

from arepy.arepy_imgui.imgui_repository import ImGui

from ..asset_store import AssetStore
from ..builders import EntityBuilder
from ..ecs.registry import Registry
from ..ecs.systems import System, SystemPipeline
from ..ecs.threading import ECS_KILL_THREAD_EVENT, run_ecs_thread_executor
from ..event_manager import EventManager
from .display import Display
from .input import Input
from .renderer.renderer_2d import Color, Renderer2D

Resources: Dict[str, Any] = {}


class ArepyEngine:
    title: str = "Arepy Engine"
    window_width: int = 1920
    window_height: int = 1080
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
        Resources[Display.__name__] = self.display
        Resources[Renderer2D.__name__] = self.renderer
        Resources[Input.__name__] = self.input
        Resources[EventManager.__name__] = self._event_manager
        Resources[AssetStore.__name__] = self._asset_store

        self._registry = Registry()
        self._registry.resources = Resources

    def init(self):
        from ..container import dependencies

        self.display.set_vsync(self.vsync)
        self.display.create_window(self.window_width, self.window_height, self.title)
        self.renderer.set_max_framerate(self.max_frame_rate)
        if self.fullscreen:
            self.display.toggle_fullscreen()
        # Imgui
        self.imgui = dependencies().imgui_repository
        self.imgui_backend_implementation = dependencies().imgui_renderer_repository()
        self._registry.resources[ImGui.__name__] = self.imgui

    def run(self):

        self.on_startup()
        # _ = Thread(target=run_ecs_thread_executor, daemon=True).start()
        while not self.display.window_should_close():
            self.__input_process()
            self.__update_process()
            self.__render_process()
        self.on_shutdown()

    def __input_process(self):
        self.imgui_backend_implementation.process_inputs()

    def __update_process(self):
        self._registry.run(pipeline=SystemPipeline.UPDATE)
        self.on_update()
        self._registry.update()

    def __render_process(self):
        self.renderer.start_frame()
        self.renderer.clear(color=Color(245, 245, 245, 255))
        self.imgui.new_frame()
        self._registry.run(pipeline=SystemPipeline.RENDER)
        self.renderer.draw_fps(position=(10, 10))
        self.on_render()
        self.renderer.end_frame()
        self.imgui.render()
        self.imgui_backend_implementation.render(self.imgui.get_draw_data())
        self.renderer.swap_buffers()

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
