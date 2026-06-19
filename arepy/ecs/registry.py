import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from inspect import isclass, iscoroutinefunction, isfunction
from types import ModuleType
from typing import Dict, List, Optional, Sequence, Set, Type

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
from .query import (
    BatchQuery,
    Query,
    get_queries_instance_from_arguments,
    get_signed_query_arguments,
)
from .systems import System, SystemPipeline, SystemState
from .utils import Signature

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ResourceMarker:
    name: str
    index: int


@dataclass(slots=True)
class Registry:
    number_of_entities: int = 0
    number_of_systems: int = 0
    component_pools: List[Optional[IComponentPool]] = field(default_factory=list)
    systems: Dict[
        SystemPipeline,
        Dict[SystemState, Set[System]],
    ] = field(
        default_factory=lambda: {
            pipeline: {state: set() for state in SystemState}
            for pipeline in SystemPipeline
        }
    )
    queries: dict[System, List[object]] = field(default_factory=dict)
    resource_markers: dict[System, List[ResourceMarker]] = field(default_factory=dict)

    entity_component_signatures: List[Signature] = field(default_factory=list)

    entities_to_be_added: Set[Entity] = field(default_factory=set)
    entities_to_be_removed: Set[Entity] = field(default_factory=set)
    entities_to_be_synced_on_remove: Set[Entity] = field(default_factory=set)
    entities_to_be_synced_on_add: Set[Entity] = field(default_factory=set)

    free_entity_ids: deque[int] = field(default_factory=deque)

    resources: dict[str, object] = field(default_factory=dict)
    global_resources: dict[str, object] = field(default_factory=dict)
    component_revision: int = 0
    component_revisions: List[int] = field(default_factory=list)
    _all_queries: List[Query] = field(default_factory=list, init=False, repr=False)
    _system_batch_queries: Dict[System, List[BatchQuery]] = field(
        default_factory=dict, init=False, repr=False
    )
    _async_systems: Set[System] = field(default_factory=set, init=False, repr=False)

    def create_entity(self) -> Entity:

        if not self.free_entity_ids:
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
        if sync_queries:
            self.entities_to_be_synced_on_add.add(entity)

        entity_id = entity._id
        entity_index = entity_id - 1
        component_id = ComponentIndex.get_type_id(component_type)
        component_index = component_id - 1
        component_pools = self.component_pools

        if component_id >= len(component_pools):
            if component_id >= MAX_COMPONENTS:
                raise MaximumComponentsExceededError(MAX_COMPONENTS)
            new_size = component_id + 1
            component_pools.extend([None] * (new_size - len(component_pools)))
            self.component_revisions.extend(
                [0] * (new_size - len(self.component_revisions))
            )

        component_pool = component_pools[component_index]
        if component_pool is None:
            component_pool = ComponentPool(component_type)
            component_pools[component_index] = component_pool

        components = component_pool._components
        if entity_id >= len(components):
            new_pool_size = max(entity_id + 1, len(components) * 2)
            components.extend([None] * (new_pool_size - len(components)))

        components[entity_index] = component
        entity._component_cache[component_type] = component
        self.entity_component_signatures[entity_index].set(component_id, True)
        self.component_revision += 1
        self.component_revisions[component_index] += 1

    def get_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> Optional[TComponent]:
        entity_index = entity._id - 1
        component_id: int = ComponentIndex.get_type_id(component_type)
        component_index = component_id - 1
        component_pools = self.component_pools
        if (
            component_index >= len(component_pools)
            or component_pools[component_index] is None
        ):
            return None

        component_pool = component_pools[component_index]
        components = component_pool._components
        if entity_index >= len(components):
            return None
        return components[entity_index]

    def remove_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> None:
        entity_id = entity._id
        component_id: int = ComponentIndex.get_type_id(component_type)
        component_index = component_id - 1
        component_pools = self.component_pools
        if (
            component_index >= len(component_pools)
            or component_pools[component_index] is None
        ):
            return

        component_pool = component_pools[component_index]
        component_pool._components[entity_id - 1] = None
        entity._component_cache.pop(component_type, None)

        self.entity_component_signatures[entity_id - 1].clear_bit(component_id)
        self.entities_to_be_synced_on_remove.add(entity)
        self.component_revision += 1
        self.component_revisions[component_index] += 1

    def get_component_revision(self) -> int:
        return self.component_revision

    def get_component_revisions(
        self, component_types: Sequence[Type[Component]]
    ) -> tuple[int, ...]:
        revisions = self.component_revisions
        result: list[int] = []
        for component_type in component_types:
            component_id = ComponentIndex.get_type_id(component_type)
            index = component_id - 1
            result.append(revisions[index] if index < len(revisions) else 0)
        return tuple(result)

    def has_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> bool:
        entity_id = entity._id
        component_id: int = ComponentIndex.get_type_id(component_type)
        return self.entity_component_signatures[entity_id - 1].test(component_id)

    def add_system(
        self, pipeline: SystemPipeline, state: SystemState, system: System
    ) -> None:
        arguments = get_signed_query_arguments(system)
        markers = self._extract_resource_markers(arguments)
        self.queries[system] = list(arguments.values())
        self.resource_markers[system] = markers
        system_queries = get_queries_instance_from_arguments(self.queries[system])
        for query in system_queries:
            query.set_registry(self)
        self._all_queries.extend(system_queries)
        self._system_batch_queries[system] = [
            query for query in system_queries if isinstance(query, BatchQuery)
        ]

        if self.systems.get(pipeline) is None:
            self.systems[pipeline] = dict()
        if not isfunction(system):
            raise ValueError("System must be a function")
        if iscoroutinefunction(system):
            self._async_systems.add(system)

        self.systems[pipeline].setdefault(state, set()).add(system)
        self.number_of_systems += 1

    def _extract_resource_markers(
        self, arguments: dict[str, object]
    ) -> List[ResourceMarker]:
        markers: List[ResourceMarker] = []
        for idx, (key, value) in enumerate(arguments.items()):
            if isclass(value) and not issubclass(value, Component):
                resource_name = value.__name__
                if value.__module__ == "builtins":
                    continue
                markers.append(ResourceMarker(resource_name, idx))
                arguments[key] = None
            elif isinstance(value, ModuleType):
                markers.append(ResourceMarker(value.__name__, idx))
                arguments[key] = None
        return markers

    def get_resource(self, resource_name: str) -> object | None:
        if resource_name in self.resources:
            return self.resources[resource_name]
        return self.global_resources.get(resource_name)

    def add_entity_to_systems(self, entity: Entity) -> None:
        self.sync_entity_queries(entity)

    def remove_entity_from_systems(self, entity: Entity) -> None:
        for query in self._all_queries:
            query.remove_entity(entity)

    def _remove_entities_from_systems(self, entities: Set[Entity]) -> None:
        for query in self._all_queries:
            query._remove_entities(entities)

    def sync_entity_queries(self, entity: Entity) -> None:
        entity_id = entity._id
        component_signature = self.entity_component_signatures[entity_id - 1]
        for query in self._all_queries:
            if query.matches(component_signature):
                query.add_entity(entity)
            else:
                query.remove_entity(entity)

    def _sync_entities_queries(self, entities: Set[Entity]) -> None:
        signatures = self.entity_component_signatures
        for query in self._all_queries:
            query._sync_entities(entities, signatures)

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
        self.systems[pipeline][prev_state].remove(system)
        if state not in self.systems[pipeline]:
            self.systems[pipeline][state] = set()

        self.systems[pipeline][state].add(system)

    # Update
    def update(self) -> None:
        removed_entities = self.entities_to_be_removed
        dirty_entities = self.entities_to_be_added | self.entities_to_be_synced_on_add
        dirty_entities.update(self.entities_to_be_synced_on_remove)
        if removed_entities:
            dirty_entities.difference_update(removed_entities)

        if dirty_entities:
            self._sync_entities_queries(dirty_entities)

        self.entities_to_be_added.clear()
        self.entities_to_be_synced_on_add.clear()
        self.entities_to_be_synced_on_remove.clear()

        if removed_entities:
            self._remove_entities_from_systems(removed_entities)
            for entity in removed_entities:
                entity_id = entity._id
                self.entity_component_signatures[entity_id - 1].clear()
                self.free_entity_ids.append(entity_id)
            removed_entities.clear()

    def run(self, pipeline: SystemPipeline) -> None:
        pipeline_systems = self.systems.get(pipeline, {})
        for system in pipeline_systems.get(SystemState.ON, ()):
            args = self._resolve_system_args(system)
            batch_queries = self._system_batch_queries[system]
            if system in self._async_systems:
                asyncio.create_task(
                    self._run_async_system(system, args, batch_queries)
                )
                continue
            system(*args)
            self._flush_batch_queries(batch_queries)

    async def _run_async_system(
        self, system: System, args: List[object], batch_queries: List[BatchQuery]
    ) -> None:
        try:
            await system(*args)
        finally:
            self._flush_batch_queries(batch_queries)

    def _resolve_system_args(self, system: System) -> List[object]:
        args = self.queries[system]
        markers = self.resource_markers.get(system, [])
        for marker in markers:
            args[marker.index] = self.get_resource(marker.name)
        for batch_query in self._system_batch_queries[system]:
            batch_query._prepare_for_system_run()
        return args

    def _flush_batch_queries(self, batch_queries: List[BatchQuery]) -> None:
        for batch_query in batch_queries:
            batch_query._flush_after_system_run()
