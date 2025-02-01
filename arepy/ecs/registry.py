import logging
from collections import deque
from dataclasses import dataclass, field
from inspect import isclass, isfunction
from typing import Dict, List, Optional, Sequence, Set, Type, cast

from .components import (
    Component,
    ComponentIndex,
    ComponentPool,
    IComponentPool,
    TComponent,
)
from .constants import MAX_COMPONENTS
from .entities import Entity
from .exceptions import MaximumComponentsExceededError
from .query import get_queries_instance_from_arguments, get_signed_query_arguments
from .systems import System, SystemPipeline, SystemState
from .utils import Signature

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Registry:
    number_of_entities: int = 0
    number_of_systems: int = 0
    component_pools: List[Optional[IComponentPool]] = field(default_factory=list)
    systems: Dict[
        SystemPipeline,
        Dict[SystemState, Set[System]],
    ] = field(default_factory=lambda: {key: {} for key in SystemPipeline})
    queries: dict[System, Sequence[object]] = field(default_factory=dict)

    entity_component_signatures: List[Signature] = field(default_factory=list)

    entities_to_be_added: Set[Entity] = field(default_factory=set)
    entities_to_be_removed: Set[Entity] = field(default_factory=set)
    entities_to_be_synced_on_remove: Set[tuple[Entity, Component]] = field(
        default_factory=set
    )
    entities_to_be_synced_on_add: Set[tuple[Entity, Component]] = field(
        default_factory=set
    )

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
        sync_queries: bool = False,
    ) -> None:
        logger.debug(f"Adding component {component_type.__name__} to entity {entity}.")

        if sync_queries:
            self.entities_to_be_synced_on_add.add((entity, component))

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
        if component_id - 1 > len(self.component_pools):
            return

        component_pool = cast(
            ComponentPool[Component],
            self.component_pools[component_id - 1],
        )
        component_pool.set(entity.get_id() - 1, None)  # type: ignore

        self.entity_component_signatures[entity_id - 1].clear_bit(component_id)
        self.entities_to_be_synced_on_remove.add(
            (entity, cast(Component, component_type))
        )

    def has_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> bool:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)
        return self.entity_component_signatures[entity_id - 1].test(component_id)

    # System management
    def add_system(
        self, pipeline: SystemPipeline, state: SystemState, system: System
    ) -> None:

        arguments = get_signed_query_arguments(system)
        self._fill_arguments_with_resources(arguments)
        self.queries[system] = list(arguments.values())
        #  System Pipeline -> State -> (System, arguments)

        if self.systems.get(pipeline) is None:
            self.systems[pipeline] = dict()
        if not isfunction(system):
            raise ValueError("System must be a function")

        self.systems[pipeline].setdefault(state, set()).add(system)
        self.number_of_systems += 1

    def _fill_arguments_with_resources(self, arguments: dict) -> None:
        for key, value in arguments.copy().items():
            for resource_name, _ in self.resources.items():
                if isclass(value) and resource_name == value.__name__:
                    resource_value = self.resources[resource_name]
                    arguments[key] = resource_value

    def add_entity_to_systems(self, entity: Entity) -> None:
        entity_id: int = entity.get_id()
        entity_component_signature: Signature = self.entity_component_signatures[
            entity_id - 1
        ]
        self.sync_queries_on_add_component(entity, entity_component_signature)

    def remove_entity_from_systems(self, entity: Entity) -> None:
        for arguments in self.queries.values():
            queries = get_queries_instance_from_arguments(arguments)
            for query in queries:
                query.remove_entity(entity)

    def sync_queries_on_add_component(
        self, entity: Entity, component_signature: Signature
    ) -> None:
        for arguments in self.queries.values():
            affected_queries = get_queries_instance_from_arguments(arguments)
            for affected_query in affected_queries:
                if affected_query.get_component_signature().matches(
                    component_signature
                ):
                    affected_query.add_entity(entity)

    def sync_queries_on_remove_component(
        self,
        entity: Entity,
        component: Component,
    ) -> None:
        component_signature = Signature(MAX_COMPONENTS)
        component_id = ComponentIndex.get_id(component.__name__)  # type: ignore
        component_signature.set(component_id, True)

        for query in self.queries.values():
            affected_queries = get_queries_instance_from_arguments(query)
            for affected_query in affected_queries:
                if component_signature.matches(
                    affected_query.get_component_signature()
                ):
                    affected_query.remove_entity(entity)

    def kill_entity(self, entity: Entity) -> None:
        self.entities_to_be_removed.add(entity)

    def set_system_state(
        self, pipeline: SystemPipeline, system: System, state: SystemState
    ) -> None:
        prev_state = [
            state
            for state, systems in self.systems[pipeline].items()
            if system in systems
        ]
        if len(prev_state) == 0:
            raise ValueError(f"System {system} not found in pipeline {pipeline}")

        prev_state = prev_state[0]
        self.systems[pipeline][state] = self.systems[pipeline].pop(prev_state, set())

    # Update
    def update(self) -> None:

        if len(self.entities_to_be_synced_on_add) > 0:
            for entity, component in self.entities_to_be_synced_on_add:
                self.sync_queries_on_add_component(
                    entity, self.entity_component_signatures[entity.get_id() - 1]
                )
            self.entities_to_be_synced_on_add.clear()

        if len(self.entities_to_be_synced_on_remove) > 0:
            for entity, component in self.entities_to_be_synced_on_remove:
                self.sync_queries_on_remove_component(entity, component)
            self.entities_to_be_synced_on_remove.clear()

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
        for state, systems in self.systems[pipeline].items():
            # Need to improve the threading system by handling concurrency issues and optimizing performance
            # maybe spliting the queries in chunks of entities
            # if pipeline == SystemPipeline.UPDATE:
            #   ECS_EXECUTOR_QUEUE.put_nowait((system, self.queries[system]))
            if state == SystemState.OFF:
                continue
            for system in systems:
                system(*self.queries[system])
