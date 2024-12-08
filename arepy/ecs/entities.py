from typing import NewType, Set, Type

from .components import TComponent
from .exceptions import ComponentNotFoundError, RegistryNotSetError

try:
    from .registry import Registry
except ImportError:
    ...
Entities = NewType("Entities", Set["Entity"])


class Entity:
    __slots__ = ["_id", "_registry", "_component_cache"]

    def __init__(self, id: int, registry: "Registry"):
        self._id = id
        self._registry = registry
        self._component_cache = {}

    def get_id(self) -> int:
        return self._id

    def get_component(self, component_type: Type[TComponent]) -> TComponent:
        if self._registry is None:
            raise RegistryNotSetError

        if component := self._component_cache.get(component_type):
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

        if component_type in self._component_cache:
            del self._component_cache[component_type]

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
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
