import asyncio
from os import PathLike
from types import ModuleType
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast, overload

from arepy_ecs import World
from arepy_ecs.systems import SystemPipeline

from arepy.engine.audio import AudioDevice
from arepy.engine.input import Input

from ..asset_store import AssetStore
from ..event_manager import EventManager
from .animator import Animator
from .display import Display, WindowFlag
from .renderer.renderer_2d import Renderer2D
from .renderer.renderer_3d import Renderer3D
from .time import Time, Timers

T = TypeVar("T")
WorldCallback = Callable[[], None]


def _resource_name(resource: object) -> str:
    resource_with_name = cast(Any, resource)
    try:
        return resource_with_name.__name__
    except AttributeError:
        return type(resource).__name__


def _initialize_world_resources(world: World) -> None:
    world.add_resource(world)
    world.add_resource(Animator())
    world.add_resource(Timers())


def _emit_world_callbacks(world: World, callback_attr: str) -> None:
    callbacks = cast(list[WorldCallback], getattr(world, callback_attr))
    for callback in callbacks:
        callback()


def _advance_world_frame_services(world: World, time_resource: Time) -> None:
    animator = cast(Animator | None, world.get_world_resource(Animator))
    timers = cast(Timers | None, world.get_world_resource(Timers))
    if animator is None:
        raise KeyError("World resource 'Animator' not found")
    if timers is None:
        raise KeyError("World resource 'Timers' not found")
    timers.tick(time_resource.elapsed_seconds)
    animator.tick(time_resource.elapsed_seconds)


class ArepyEngine:

    def __init__(
        self,
        title: str = "Arepy Engine",
        width: int = 1920 // 3,
        height: int = 1080 // 3,
        max_frame_rate: int = 800,
        fullscreen: bool = False,
        icon_path: Optional[PathLike[str]] = None,
        window_flags: Optional[WindowFlag] = None,
    ):
        from ..container import dependencies

        self.title = title
        self.window_width = width
        self.window_height = height
        self.max_frame_rate = max_frame_rate
        self.fullscreen = fullscreen
        self.icon_path = icon_path
        self.window_flags = window_flags
        self._asset_store = AssetStore()
        self._event_manager = EventManager()
        self.display = dependencies().display_repository
        self.renderer_2d = dependencies().renderer_repository
        self.renderer_3d = dependencies().renderer_3d_repository
        self.input = dependencies().input_repository
        self.audio_device = dependencies().audio_device_repository
        self._global_resources: Dict[str, Any] = {}
        self._register_global_resource(Display.__name__, self.display)
        self._register_global_resource(Renderer2D.__name__, self.renderer_2d)
        self._register_global_resource(Renderer3D.__name__, self.renderer_3d)
        self._register_global_resource(AssetStore.__name__, self._asset_store)
        self._register_global_resource(Input.__name__, self.input)
        self._register_global_resource(self.__class__.__name__, self)
        self._register_global_resource(AudioDevice.__name__, self.audio_device)
        self._register_global_resource(EventManager.__name__, self._event_manager)
        self.worlds: Dict[str, World] = {}
        self._current_world: World = None  # type: ignore
        self._next_world_to_set: str = None  # type: ignore

        self._init_window()
        self._time = Time(self.display.get_time())
        self._register_global_resource(Time.__name__, self._time)

    def _init_window(self) -> None:
        from ..container import dependencies

        self.display.set_window_state(self.window_flags or WindowFlag(0))
        self.display.create_window(self.window_width, self.window_height, self.title)
        self.renderer_2d.set_max_framerate(self.max_frame_rate)
        if self.fullscreen:
            self.display.toggle_fullscreen()
        if self.icon_path:
            self.display.set_window_icon(self.icon_path)
        self.audio_device.init_device()

        self.imgui = dependencies().imgui_module
        imgui_backend_factory = dependencies().imgui_backend_factory
        self.imgui_backend = (
            imgui_backend_factory() if imgui_backend_factory is not None else None
        )
        if self.imgui is not None:
            self._register_global_resource(_resource_name(self.imgui), self.imgui)

    def _register_global_resource(self, class_name: str, resource: object) -> None:
        self._global_resources[class_name] = resource

    def run(self):
        self.on_startup()
        self.__check_and_set_world()
        while not self.display.window_should_close():
            self.__next_frame()
            self.__check_and_set_world()
        self.__shutdown_current_world()
        self.on_shutdown()

    async def run_async(self):
        self.on_startup()
        self.__check_and_set_world()
        # await run_ecs_thread_executor()
        while not self.display.window_should_close():
            self.__next_frame()
            self.__check_and_set_world()
            await asyncio.sleep(0)
        self.__shutdown_current_world()
        self.on_shutdown()

    def __next_frame(self):
        self._time.advance(self.display.get_time())
        if not self._current_world:
            self.renderer_2d.swap_buffers()
            return
        # Process input, update and render
        self.__input_process()
        self.__update_process()
        self.__render_process()

    def __check_and_set_world(self):
        if self._next_world_to_set:
            next_world = self.worlds[self._next_world_to_set]
            self._next_world_to_set = None  # type: ignore
            if self._current_world is next_world:
                return
            if self._current_world is not None:
                _emit_world_callbacks(self._current_world, "_shutdown_callbacks")
            self._current_world = next_world
            _emit_world_callbacks(self._current_world, "_startup_callbacks")

    def __shutdown_current_world(self):
        if self._current_world is not None:
            _emit_world_callbacks(self._current_world, "_shutdown_callbacks")
            self._next_world_to_set = None  # type: ignore

    def __input_process(self):
        # dispatch input events
        # self.input.pool_events()
        if self.imgui_backend is not None:
            self.imgui_backend.process_inputs()
        self._current_world.get_registry().run(pipeline=SystemPipeline.INPUT)

    def __update_process(self):
        current_world = self._current_world
        _advance_world_frame_services(current_world, self._time)
        self.__process_events_before_update()
        registry = current_world.get_registry()
        registry.update()
        registry.run(pipeline=SystemPipeline.UPDATE)
        _emit_world_callbacks(current_world, "_update_callbacks")
        self.on_update()
        self.__process_events_after_update()

    def __process_events_before_update(self) -> None:
        self._event_manager.process_events()

    def __process_events_after_update(self) -> None:
        self._event_manager.process_events()

    def __render_process(self):
        # self.renderer_2d.clear(color=Color(245, 245, 245, 255))
        # perform trick
        current_world = self._current_world
        if self.imgui is not None and self.imgui_backend is not None:
            self.imgui.new_frame()
        registry = current_world.get_registry()
        registry.run(pipeline=SystemPipeline.RENDER)
        registry.run(pipeline=SystemPipeline.RENDER_UI)
        _emit_world_callbacks(current_world, "_render_callbacks")
        self.on_render()
        if self.imgui is not None and self.imgui_backend is not None:
            self.imgui.render()
            self.imgui_backend.render(self.imgui.get_draw_data())
        self.renderer_2d.swap_buffers()

    def get_asset_store(self) -> AssetStore:
        """Get the asset store."""
        return self._asset_store

    def get_event_manager(self) -> EventManager:
        """Get the event manager."""
        return self._event_manager

    def add_resource(self, resource: object) -> None:
        if not isinstance(resource, object) or isinstance(
            resource, (int, float, str, bool, type(None))
        ):
            raise TypeError("Resource must be a class instance")
        if callable(resource) and not hasattr(resource, "__class__"):
            raise TypeError("Resource cannot be a function")
        resource_name = _resource_name(resource)
        if resource_name in self._global_resources:
            raise ValueError(f"Resource '{resource_name}' already exists")
        self._global_resources[resource_name] = resource

    @overload
    def get_resource(self, resource_type: Type[T]) -> T: ...

    @overload
    def get_resource(self, resource_type: ModuleType) -> ModuleType: ...

    def get_resource(self, resource_type: Type[T] | ModuleType) -> T | ModuleType:
        """Get a resource by its type.

        Args:
            resource_type: The class type of the resource to retrieve.

        Returns:
            The resource instance.

        Raises:
            KeyError: If the resource is not found.
        """
        resource_name = _resource_name(resource_type)
        if resource_name not in self._global_resources:
            raise KeyError(f"Resource '{resource_name}' not found")
        return self._global_resources[resource_name]

    def create_world(self, name: str) -> World:
        """Add a world to the engine.

        Args:
            name: The name of the world.
        """
        if name in self.worlds:
            raise ValueError(f"World with name {name} already exists")
        world = World(name, global_resources=self._global_resources)
        _initialize_world_resources(world)
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
