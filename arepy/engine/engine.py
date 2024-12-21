import asyncio
from threading import Thread
from typing import Any, Dict

from arepy.arepy_imgui.imgui_repository import ImGui

from ..asset_store import AssetStore
from ..builders import EntityBuilder
from ..ecs.registry import Registry
from ..ecs.systems import System, SystemPipeline
from ..event_manager import EventManager
from ..event_manager.handlers import InputEventHandler
from .display import Display
from .input import Input
from .renderer.renderer_2d import Color, Renderer2D

Resources: Dict[str, Any] = {}

InputDispatchThread = None


class ArepyEngine:
    title: str = "Arepy Engine"
    window_width: int = 1920 // 3
    window_height: int = 1080 // 3
    render_size = (window_width, window_height)
    max_frame_rate: int = 800
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
        # Necessary for input dispatching
        # add resources
        Resources[Display.__name__] = self.display
        Resources[Renderer2D.__name__] = self.renderer
        Resources[EventManager.__name__] = self._event_manager
        Resources[InputEventHandler.__name__] = InputEventHandler(self._event_manager)
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
        self.imgui_backend = dependencies().imgui_renderer_repository(
            self._event_manager
        )
        self._registry.resources[ImGui.__name__] = self.imgui
        self.input.event_manager = self._event_manager
        self.input.register_dispatchers()

    def run(self):

        self.on_startup()
        # _ = Thread(target=run_ecs_thread_executor, daemon=True).start()
        while not self.display.window_should_close():
            self.__input_process()
            self.__update_process()
            self.__render_process()
        self.on_shutdown()

    async def run_async(self):
        self.on_startup()
        # await run_ecs_thread_executor()
        while not self.display.window_should_close():
            self.__input_process()
            self.__update_process()
            self.__render_process()
            await asyncio.sleep(0)
        self.on_shutdown()

    def __input_process(self):
        # dispatch input events
        self._event_manager.process_events()
        self.imgui_backend.process_inputs()
        self._registry.run(pipeline=SystemPipeline.INPUT)

    def __update_process(self):
        self._registry.update()
        self._registry.run(pipeline=SystemPipeline.UPDATE)
        self.on_update()

    def __render_process(self):
        self.renderer.clear(color=Color(245, 245, 245, 255))
        self._registry.run(pipeline=SystemPipeline.RENDER)
        self._registry.run(pipeline=SystemPipeline.RENDER_UI)
        self.on_render()
        self.imgui_backend.render(self.imgui.get_draw_data())
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
