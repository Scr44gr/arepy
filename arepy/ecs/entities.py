import builtins
from typing import NewType, Set, Type

from .components import Component, TComponent
from .exceptions import ComponentNotFoundError, RegistryNotSetError

try:
    from .registry import Registry
except ImportError:
    ...
Entities = NewType("Entities", Set["Entity"])


class Entity:
    __slots__ = [
        "_id",
        "_registry",
        "_component_cache",
        "_generation",
        "_registry_token",
    ]

    def __init__(
        self, id: int, registry: "Registry", *, _generation: int | None = None
    ):
        self._id = id
        self._registry = registry
        self._component_cache = {}
        self._generation = (
            _generation
            if _generation is not None
            else registry._generation_for_entity_id(id)
            if registry is not None
            else 0
        )
        self._registry_token = builtins.id(registry)

    def get_id(self) -> int:
        return self._id

    def get_component(self, component_type: Type[TComponent]) -> TComponent:
        if self._registry is None:
            raise RegistryNotSetError

        component = self._component_cache.get(component_type)
        if component is not None:
            return component

        component = self._registry.get_component(self, component_type)
        if component is None:
            raise ComponentNotFoundError(component_type)

        self._component_cache[component_type] = component
        return component

    def remove_component(self, component_type: Type[TComponent]) -> None:
        if self._registry is None:
            raise RegistryNotSetError
        self._registry.remove_component(self, component_type)

        self._component_cache.pop(component_type, None)

    def add_component(self, component: Component) -> None:
        component_type = type(component)
        if self._registry is None:
            raise RegistryNotSetError
        if component_type in self._component_cache:
            return

        self._registry.add_component(self, component_type, component, sync_queries=True)

    def has_component(self, component_type: Type[TComponent]) -> bool:
        if self._registry is None:
            raise RegistryNotSetError
        return self._registry.has_component(self, component_type)

    def kill(self) -> None:
        if self._registry is None:
            raise RegistryNotSetError
        self._component_cache.clear()
        self._registry.kill_entity(self)

    def __repr__(self) -> str:
        return f"Entity(id={self._id})"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: "Entity") -> bool:
        if not isinstance(other, Entity):
            return False
        return (
            self._id == other._id
            and self._generation == other._generation
            and self._registry_token == other._registry_token
        )

    def __hash__(self) -> int:
        # Registries never contain two live generations of the same slot, so the
        # compact entity ID remains the fastest useful hash for internal sets.
        return self._id

    def _detach(self) -> None:
        """Invalidate this handle after its registry slot is recycled."""

        self._component_cache.clear()
        self._registry = None
