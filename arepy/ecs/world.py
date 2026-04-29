from types import ModuleType
from typing import Callable, Dict, List, Optional, Set, Type, TypeVar, cast, overload

from ..engine.animator import Animator
from ..engine.time import Time, Timers
from .builders import EntityBuilder
from .registry import Registry
from .systems import System, SystemPipeline, SystemState

T = TypeVar("T")
WorldCallback = Callable[[], None]


def _resource_name(resource: object) -> str:
    return getattr(resource, "__name__", resource.__class__.__name__)


class World:

    def __init__(self, name: str, global_resources: Optional[Dict[str, object]] = None):
        self._resources: Dict[str, object] = {
            self.__class__.__name__: self,
            Animator.__name__: Animator(),
            Timers.__name__: Timers(),
        }
        self._global_resources = (
            global_resources if global_resources is not None else {}
        )
        self._registry = Registry(
            resources=self._resources,
            global_resources=self._global_resources,
        )
        self.name = name
        self._startup_callbacks: List[WorldCallback] = []
        self._update_callbacks: List[WorldCallback] = []
        self._shutdown_callbacks: List[WorldCallback] = []
        self._render_callbacks: List[WorldCallback] = []

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
        self._registry.add_system(pipeline, SystemState.ON, system)

    def add_systems(self, pipeline: SystemPipeline, systems: Set[System]) -> None:
        """Create multiple systems.

        Args:
            pipeline: A pipeline to add the system.
            systems: A list of systems.
        """
        for system in systems:
            self.add_system(pipeline, system)

    def add_system_with_state(
        self, pipeline: SystemPipeline, system: System, state: SystemState
    ) -> None:
        """Create a new system with a state.

        Args:
            pipeline: A pipeline to add the system.
            system: A system.
            state: A state.
        """
        self._registry.add_system(pipeline, state, system)

    def set_system_state(
        self, pipeline: SystemPipeline, system: System, state: SystemState
    ) -> None:
        """Set the state of a system.

        Args:
            pipeline: The pipeline of the system.
            system: A system.
            state: A state.
        """
        self._registry.set_system_state(pipeline, system, state)

    def get_registry(self) -> Registry:
        """Get ECS the registry.

        Returns:
            The registry.
        """
        return self._registry

    def add_resource(self, resource: object) -> None:
        if not isinstance(resource, object) or isinstance(
            resource, (int, float, str, bool, type(None))
        ):
            raise TypeError("Resource must be a class instance")
        if callable(resource) and not hasattr(resource, "__class__"):
            raise TypeError("Resource cannot be a function")

        resource_name = _resource_name(resource)
        if resource_name in self._resources:
            raise ValueError(f"Resource '{resource_name}' already exists")
        self._resources[resource_name] = resource

    @overload
    def get_resource(self, resource_type: Type[T]) -> T: ...

    @overload
    def get_resource(self, resource_type: ModuleType) -> ModuleType: ...

    def get_resource(self, resource_type: Type[T] | ModuleType) -> T | ModuleType:
        resource_name = _resource_name(resource_type)
        if resource_name in self._resources:
            return cast(T, self._resources[resource_name])
        if resource_name in self._global_resources:
            return cast(T, self._global_resources[resource_name])
        raise KeyError(f"Resource '{resource_name}' not found")

    @overload
    def get_world_resource(self, resource_type: Type[T]) -> T: ...

    @overload
    def get_world_resource(self, resource_type: ModuleType) -> ModuleType: ...

    def get_world_resource(self, resource_type: Type[T] | ModuleType) -> T | ModuleType:
        resource_name = _resource_name(resource_type)
        if resource_name not in self._resources:
            raise KeyError(f"World resource '{resource_name}' not found")
        return cast(T, self._resources[resource_name])

    @overload
    def get_global_resource(self, resource_type: Type[T]) -> T: ...

    @overload
    def get_global_resource(self, resource_type: ModuleType) -> ModuleType: ...

    def get_global_resource(
        self, resource_type: Type[T] | ModuleType
    ) -> T | ModuleType:
        resource_name = _resource_name(resource_type)
        if resource_name not in self._global_resources:
            raise KeyError(f"Global resource '{resource_name}' not found")
        return cast(T, self._global_resources[resource_name])

    def on_startup(self, callback: WorldCallback) -> WorldCallback:
        self._startup_callbacks.append(callback)
        return callback

    def on_update(self, callback: WorldCallback) -> WorldCallback:
        self._update_callbacks.append(callback)
        return callback

    def on_shutdown(self, callback: WorldCallback) -> WorldCallback:
        self._shutdown_callbacks.append(callback)
        return callback

    def on_render(self, callback: WorldCallback) -> WorldCallback:
        self._render_callbacks.append(callback)
        return callback

    def _emit_startup(self) -> None:
        self._emit_callbacks(self._startup_callbacks)

    def _emit_update(self) -> None:
        self._emit_callbacks(self._update_callbacks)

    def _emit_shutdown(self) -> None:
        self._emit_callbacks(self._shutdown_callbacks)

    def _emit_render(self) -> None:
        self._emit_callbacks(self._render_callbacks)

    def _advance_frame_services(self, time_resource: Time) -> None:
        animator = self.get_world_resource(Animator)
        timers = self.get_world_resource(Timers)
        timers.tick(time_resource.elapsed_seconds)
        animator.tick(time_resource.elapsed_seconds)

    def _emit_callbacks(self, callbacks: List[WorldCallback]) -> None:
        for callback in callbacks:
            callback()
