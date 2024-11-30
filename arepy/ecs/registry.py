import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Type, cast

from .components import ComponentIndex, ComponentPool, IComponentPool, TComponent
from .constants import MAX_COMPONENTS
from .exceptions import (
    ComponentNotFoundError,
    MaximumComponentsExceededError,
    RegistryNotSetError,
)
from .query import get_query_from_args, make_query_signature
from .systems import System, SystemPipeline
from .utils import Signature

logger = logging.getLogger(__name__)


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


@dataclass(slots=True)
class Registry:
    number_of_entities: int = 0
    component_pools: List[Optional[IComponentPool]] = field(default_factory=list)
    systems: Dict[SystemPipeline, Set[System]] = field(default_factory=dict)
    # TODO: make the queries type hints more robust
    queries: dict[System, dict] = field(default_factory=dict)
    entity_component_signatures: List[Signature] = field(default_factory=list)

    entities_to_be_added: Set[Entity] = field(default_factory=set)
    entities_to_be_removed: Set[Entity] = field(default_factory=set)
    free_entity_ids: deque[int] = field(default_factory=deque)

    # resources
    resources: dict[str, object] = field(default_factory=dict)

    def create_entity(self) -> Entity:

        if len(self.free_entity_ids) == 0:
            self.number_of_entities += 1
            entity_id = self.number_of_entities
            if entity_id >= len(self.entity_component_signatures):
                self.entity_component_signatures.extend([Signature(MAX_COMPONENTS)])
        else:
            entity_id = self.free_entity_ids.popleft()

        entity = Entity(entity_id, self)
        self.entities_to_be_added.add(entity)
        return entity

    # Component management
    def add_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
        component: TComponent,
    ) -> None:
        logger.debug(f"Adding component {component_type.__name__} to entity {entity}.")
        entity_id = entity.get_id()

        component_id = ComponentIndex.get_id(component_type.__name__)

        if component_id >= len(self.component_pools):
            if component_id >= MAX_COMPONENTS:
                raise MaximumComponentsExceededError(MAX_COMPONENTS)
            self.component_pools.extend(
                [None] * (component_id - len(self.component_pools))
            )
        if self.component_pools[component_id - 1] is None:
            self.component_pools[component_id - 1] = ComponentPool(component_type)

        component_pool = cast(
            ComponentPool[TComponent], self.component_pools[component_id - 1]
        )
        # Resize the component pool if necessary
        if entity_id >= len(component_pool):
            component_pool.extend([None] * (entity_id - len(component_pool) + 1))
        # Set the component to the pool
        component_pool.set(entity_id - 1, component)

        self.entity_component_signatures[entity_id - 1].set(component_id, True)

    def get_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> Optional[TComponent]:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)
        if (
            component_id > len(self.component_pools)
            or self.component_pools[component_id - 1] is None
        ):
            return None

        component_pool: ComponentPool[TComponent] = cast(
            ComponentPool[TComponent], self.component_pools[component_id - 1]
        )
        return component_pool.get(entity_id - 1)

    def remove_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> None:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)
        self.entity_component_signatures[entity_id - 1].clear_bit(component_id)

    def has_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> bool:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)

        return self.entity_component_signatures[entity_id - 1].test(component_id)

    # System management
    def add_system(self, pipeline: SystemPipeline, system: System, **kwargs) -> None:

        if type(system) is tuple:
            assert isinstance(system, tuple)
            for callback in system:
                arguments = make_query_signature(callback)
                self.queries[callback] = arguments
        else:
            arguments = make_query_signature(system)  # type: ignore
            # fill arguments with the resources
            for argument in arguments.copy():
                for resource in self.resources:
                    try:

                        if resource == argument.__name__:  # type: ignore
                            arguments[self.resources[resource]] = arguments.pop(
                                argument
                            )
                    except AttributeError:
                        continue
            self.queries[system] = arguments

        if self.systems.get(pipeline) is None:
            self.systems[pipeline] = set()

        self.systems[pipeline].add(system)

    def add_entity_to_systems(self, entity: Entity) -> None:
        entity_id: int = entity.get_id()
        entity_component_signature: Signature = self.entity_component_signatures[
            entity_id - 1
        ]

        for arguments in self.queries.values():
            query = get_query_from_args(arguments)
            if query.get_component_signature().matches(entity_component_signature):
                query.add_entity(entity)

    def remove_entity_from_systems(self, entity: Entity) -> None:
        for arguments in self.queries.values():
            query = get_query_from_args(arguments)
            query.remove_entity(entity)

    def kill_entity(self, entity: Entity) -> None:
        self.entities_to_be_removed.add(entity)

    def remove_system(self, pipeline: SystemPipeline, system: System) -> None:
        self.systems[pipeline].remove(system)

    def has_system(self, system: System) -> bool:
        return system in self.systems

    # Update
    def update(self) -> None:

        if len(self.entities_to_be_added) > 0:
            for entity in self.entities_to_be_added:
                self.add_entity_to_systems(entity)
            self.entities_to_be_added.clear()

        if len(self.entities_to_be_removed) > 0:
            for entity in self.entities_to_be_removed:
                self.remove_entity_from_systems(entity)
                self.entity_component_signatures[entity.get_id() - 1].clear()
                self.free_entity_ids.append(entity.get_id())
            self.entities_to_be_removed.clear()

    def run(self, pipeline: SystemPipeline) -> None:
        for system in self.systems[pipeline]:
            system(*self.queries[system])  # type: ignore
