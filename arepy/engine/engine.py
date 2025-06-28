import asyncio
from typing import Any, Dict

from arepy.arepy_imgui.imgui_repository import Imgui
from arepy.ecs.world import World
from arepy.engine.audio import AudioDevice
from arepy.engine.input import Input

from ..asset_store import AssetStore
from ..ecs.systems import SystemPipeline
from ..event_manager import EventManager
from .display import Display
from .renderer.renderer_2d import Color, Renderer2D
from .renderer.renderer_3d import Renderer3D

Resources: Dict[str, Any] = {}


class ArepyEngine:
    title: str = "Arepy Engine"
    window_width: int = 1920 // 3
    window_height: int = 1080 // 3
    max_frame_rate: int = 800
    debug: bool = False
    fullscreen: bool = False
    vsync: bool = False

    def __init__(self):
        from ..container import dependencies

        global Resources

        self._asset_store = AssetStore()
        self._event_manager = EventManager()
        self.display = dependencies().display_repository
        self.renderer = dependencies().renderer_repository
        self.renderer_3d = dependencies().renderer_3d_repository
        self.input = dependencies().input_repository
        self.audio_device = dependencies().audio_device_repository
        Resources[Display.__name__] = self.display
        Resources[Renderer2D.__name__] = self.renderer
        Resources[Renderer3D.__name__] = self.renderer_3d
        Resources[AssetStore.__name__] = self._asset_store
        Resources[Input.__name__] = self.input
        Resources[ArepyEngine.__name__] = self
        Resources[AudioDevice.__name__] = self.audio_device
        Resources[EventManager.__name__] = self._event_manager
        self.worlds: Dict[str, World] = {}
        self._current_world: World = None  # type: ignore
        self._next_world_to_set: str = None  # type: ignore

    def init(self):
        from ..container import dependencies

        self.display.set_vsync(self.vsync)
        self.display.create_window(self.window_width, self.window_height, self.title)
        self.renderer.set_max_framerate(self.max_frame_rate)
        if self.fullscreen:
            self.display.toggle_fullscreen()
        # init audio device
        self.audio_device.init_device()

        # Imgui
        self.imgui = dependencies().imgui_repository
        self.imgui_backend = dependencies().imgui_renderer_repository()
        Resources[Imgui.__name__] = self.imgui

    def run(self):
        self.on_startup()
        while not self.display.window_should_close():
            self.__next_frame()
            self.__check_and_set_world()
        self.on_shutdown()

    async def run_async(self):
        self.on_startup()
        # await run_ecs_thread_executor()
        while not self.display.window_should_close():
            self.__next_frame()
            self.__check_and_set_world()
            await asyncio.sleep(0)
        self.on_shutdown()

    def __next_frame(self):
        if not self._current_world:
            self.renderer.swap_buffers()
            return
        # Process input, update and render
        self.__input_process()
        self.__update_process()
        self.__render_process()

    def __check_and_set_world(self):
        if self._next_world_to_set:
            self._current_world = self.worlds[self._next_world_to_set]
            self._next_world_to_set = None  # type: ignore

    def __input_process(self):
        # dispatch input events
        # self.input.pool_events()
        self.imgui_backend.process_inputs()
        self._current_world._registry.run(pipeline=SystemPipeline.INPUT)

    def __update_process(self):
        current_world = self._current_world
        current_world._registry.update()
        current_world._registry.run(pipeline=SystemPipeline.UPDATE)
        self.on_update()

    def __render_process(self):
        self.renderer.clear(color=Color(245, 245, 245, 255))
        # perform trick
        current_world = self._current_world
        current_world._registry.run(pipeline=SystemPipeline.RENDER)
        current_world._registry.run(pipeline=SystemPipeline.RENDER_UI)
        self.on_render()
        self.imgui_backend.render(self.imgui.get_draw_data())
        self.renderer.swap_buffers()

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

    def create_world(self, name: str) -> World:
        """Add a world to the engine.

        Args:
            name: The name of the world.
        """
        if name in self.worlds:
            raise ValueError(f"World with name {name} already exists")

        world = World(name)
        # Add resources to the world
        ecs_registry = world.get_registry()
        ecs_registry.resources = Resources
        self.worlds[name] = world
        return world

    def set_current_world(self, name: str) -> None:
        """Set the current world.

        Args:
            name: The name of the world.
        """
        if name not in self.worlds:
            raise ValueError(f"World with name {name} does not exist")
        self._next_world_to_set = name

    def get_current_world(self) -> World:
        """Get the current world.

        Returns:
            The current world.
        """
        return self._current_world

    def remove_world(self, name: str) -> World:
        """Remove a world from the engine.

        (this will not delete the world, just remove it from the engine.)

        Args:
            name: The name of the world.
        """
        if name not in self.worlds:
            raise ValueError(f"World with name {name} does not exist")
        return self.worlds.pop(name)

    # Engine func Events
    def on_startup(self): ...
    def on_update(self): ...
    def on_shutdown(self): ...
    def on_render(self): ...
