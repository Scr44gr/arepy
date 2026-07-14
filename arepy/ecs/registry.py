import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from inspect import isclass, iscoroutinefunction
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
    _async_tasks: Dict[System, asyncio.Task[None]] = field(
        default_factory=dict, init=False, repr=False
    )
    _entity_slots: List[Optional[Entity]] = field(
        default_factory=list, init=False, repr=False
    )
    _entity_generations: List[int] = field(
        default_factory=list, init=False, repr=False
    )
    _system_order: Dict[SystemPipeline, List[System]] = field(
        default_factory=lambda: {pipeline: [] for pipeline in SystemPipeline},
        init=False,
        repr=False,
    )

    def create_entity(self) -> Entity:
        free_entity_ids = self.free_entity_ids
        signatures = self.entity_component_signatures
        entity_slots = self._entity_slots
        generations = self._entity_generations

        if not free_entity_ids:
            entity_id = self.number_of_entities + 1
            self.number_of_entities = entity_id
            entity_index = entity_id - 1
            if entity_index >= len(signatures):
                signatures.append(Signature(MAX_COMPONENTS + 1))
                entity_slots.append(None)
                generations.append(0)
        else:
            entity_id = free_entity_ids.popleft()
            entity_index = entity_id - 1

        entity = Entity(
            entity_id,
            self,
            _generation=generations[entity_index],
        )
        entity_slots[entity_index] = entity
        self.entities_to_be_added.add(entity)
        return entity

    def _generation_for_entity_id(self, entity_id: int) -> int:
        entity_index = entity_id - 1
        if 0 <= entity_index < len(self._entity_generations):
            return self._entity_generations[entity_index]
        return 0

    def _is_current_entity(self, entity: Entity) -> bool:
        entity_index = entity._id - 1
        if entity._registry is not self or not 0 <= entity_index < len(
            self._entity_slots
        ):
            return False

        current_entity = self._entity_slots[entity_index]
        return current_entity is entity or (
            current_entity is not None
            and entity._generation == self._entity_generations[entity_index]
        )

    # Component management
    def add_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
        component: TComponent,
        sync_queries: bool = False,
    ) -> None:
        entity_id = entity._id
        entity_index = entity_id - 1
        entity_slots = self._entity_slots
        if (
            not 0 <= entity_index < len(entity_slots)
            or entity_slots[entity_index] is not entity
        ) and not self._is_current_entity(entity):
            raise ValueError("Entity is not alive in this registry.")
        if sync_queries or entity not in self.entities_to_be_added:
            self.entities_to_be_synced_on_add.add(entity)

        component_id = ComponentIndex.get_type_id(component_type)
        component_index = component_id - 1
        component_pools = self.component_pools

        if component_id >= len(component_pools):
            if component_id > MAX_COMPONENTS:
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
        elif component_pool._component_type is not component_type:
            raise TypeError(
                "Component types with the same class name cannot share a Registry: "
                f"{component_pool._component_type!r} and {component_type!r}."
            )

        components = component_pool._components
        if entity_index >= len(components):
            new_pool_size = max(entity_index + 1, max(1, len(components) * 2))
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
        if not self._is_current_entity(entity):
            return None
        entity_index = entity._id - 1
        component_id = ComponentIndex.try_get_type_id(component_type)
        if component_id is None:
            return None
        component_index = component_id - 1
        component_pools = self.component_pools
        if (
            component_index >= len(component_pools)
            or component_pools[component_index] is None
        ):
            return None

        component_pool = component_pools[component_index]
        if component_pool._component_type is not component_type:
            return None
        components = component_pool._components
        if entity_index >= len(components):
            return None
        return components[entity_index]

    def remove_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> None:
        if not self._is_current_entity(entity):
            return
        entity_id = entity._id
        entity_index = entity_id - 1
        component_id = ComponentIndex.try_get_type_id(component_type)
        if component_id is None:
            return
        component_index = component_id - 1
        component_pools = self.component_pools
        if (
            component_index >= len(component_pools)
            or component_pools[component_index] is None
        ):
            return

        component_pool = component_pools[component_index]
        if component_pool._component_type is not component_type:
            return
        components = component_pool._components
        if entity_index >= len(components) or components[entity_index] is None:
            return
        components[entity_index] = None
        entity._component_cache.pop(component_type, None)

        self.entity_component_signatures[entity_index].clear_bit(component_id)
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
            component_id = ComponentIndex.try_get_type_id(component_type)
            if component_id is None:
                result.append(0)
                continue
            index = component_id - 1
            result.append(revisions[index] if index < len(revisions) else 0)
        return tuple(result)

    def has_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> bool:
        if not self._is_current_entity(entity):
            return False
        component_id = ComponentIndex.try_get_type_id(component_type)
        if component_id is None:
            return False
        component_index = component_id - 1
        if component_index >= len(self.component_pools):
            return False
        component_pool = self.component_pools[component_index]
        if (
            component_pool is None
            or component_pool._component_type is not component_type
        ):
            return False
        return self.entity_component_signatures[entity._id - 1].test(component_id)

    def add_system(
        self, pipeline: SystemPipeline, state: SystemState, system: System
    ) -> None:
        if not callable(system):
            raise ValueError("System must be a function")

        pipeline_systems = self.systems.setdefault(pipeline, {})
        current_states = [
            current_state
            for current_state, registered in pipeline_systems.items()
            if system in registered
        ]
        if current_states:
            if current_states[0] != state:
                self.set_system_state(pipeline, system, state)
            return

        if system not in self.queries:
            arguments = get_signed_query_arguments(system)
            markers = self._extract_resource_markers(arguments)
            system_args = list(arguments.values())
            system_queries = get_queries_instance_from_arguments(system_args)
            for query in system_queries:
                query.set_registry(self)

            active_entities = {
                entity
                for entity in self._entity_slots
                if entity is not None and entity not in self.entities_to_be_removed
            }
            if active_entities:
                for query in system_queries:
                    query._sync_entities(
                        active_entities, self.entity_component_signatures
                    )

            self.queries[system] = system_args
            self.resource_markers[system] = markers
            self._all_queries.extend(system_queries)
            self._system_batch_queries[system] = [
                query for query in system_queries if isinstance(query, BatchQuery)
            ]
            if iscoroutinefunction(system):
                self._async_systems.add(system)

        pipeline_systems.setdefault(state, set()).add(system)
        self._system_order.setdefault(pipeline, []).append(system)
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
        if not self._is_current_entity(entity):
            return
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
        if not self._is_current_entity(entity):
            return
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
        if not (
            self.entities_to_be_added
            or self.entities_to_be_removed
            or self.entities_to_be_synced_on_add
            or self.entities_to_be_synced_on_remove
        ):
            return

        removed_entities = self.entities_to_be_removed
        dirty_entities = set(self.entities_to_be_added)
        dirty_entities.update(self.entities_to_be_synced_on_add)
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
            removed_in_id_order = sorted(removed_entities, key=lambda item: item._id)
            cleared_components = 0
            for component_index, component_pool in enumerate(self.component_pools):
                if component_pool is None:
                    continue
                components = component_pool._components
                cleared_from_pool = 0
                for entity in removed_in_id_order:
                    entity_index = entity._id - 1
                    if (
                        entity_index < len(components)
                        and components[entity_index] is not None
                    ):
                        components[entity_index] = None
                        cleared_from_pool += 1
                if cleared_from_pool:
                    self.component_revisions[component_index] += cleared_from_pool
                    cleared_components += cleared_from_pool

            self.component_revision += cleared_components
            for entity in removed_in_id_order:
                entity_id = entity._id
                entity_index = entity_id - 1
                self.entity_component_signatures[entity_index].clear()
                active_entity = self._entity_slots[entity_index]
                if active_entity is not None:
                    active_entity._detach()
                if entity is not active_entity:
                    entity._detach()
                self._entity_slots[entity_index] = None
                self._entity_generations[entity_index] += 1
                self.free_entity_ids.append(entity_id)
            removed_entities.clear()

    def run(self, pipeline: SystemPipeline) -> None:
        pipeline_systems = self.systems.get(pipeline, {})
        enabled_systems = pipeline_systems.get(SystemState.ON, ())
        for system in self._system_order.get(pipeline, ()):
            if system not in enabled_systems:
                continue
            batch_queries = self._system_batch_queries[system]
            if system in self._async_systems:
                in_flight = self._async_tasks.get(system)
                if in_flight is not None and not in_flight.done():
                    continue
                args = list(self._resolve_system_args(system))
                task = asyncio.create_task(
                    self._run_async_system(system, args, batch_queries)
                )
                self._async_tasks[system] = task
                task.add_done_callback(
                    lambda completed, registered_system=system: self._finish_async_system(
                        registered_system, completed
                    )
                )
                continue
            args = self._resolve_system_args(system)
            try:
                system(*args)
            finally:
                self._flush_batch_queries(batch_queries)

    def _finish_async_system(
        self, system: System, task: asyncio.Task[None]
    ) -> None:
        if self._async_tasks.get(system) is task:
            self._async_tasks.pop(system, None)
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception as error:
            logger.error(
                "Async system %r failed",
                system,
                exc_info=(type(error), error, error.__traceback__),
            )

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
