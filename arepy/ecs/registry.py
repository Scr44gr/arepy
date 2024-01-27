import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, cast

from .components import ComponentIndex, ComponentPool, IComponentPool, TComponent
from .constants import MAX_COMPONENTS
from .systems import System, TSystem
from .utils import Signature

logger = logging.getLogger(__name__)


class Entity:
    def __init__(self, id: int, registry: "Registry"):
        self._id = id
        self._registry = registry

    def get_id(self) -> int:
        return self._id

    def get_component(self, component_type: Type[TComponent]) -> TComponent:
        if self._registry is None:
            raise RuntimeError("Registry is not set.")
        component = self._registry.get_component(self, component_type)
        if component is None:
            raise RuntimeError(f"Component {component_type} does not exist.")
        return component

    def remove_component(self, component_type: Type[TComponent]) -> None:
        if self._registry is None:
            raise RuntimeError("Registry is not set.")
        self._registry.remove_component(self, component_type)

    def has_component(self, component_type: Type[TComponent]) -> bool:
        if self._registry is None:
            raise RuntimeError("Registry is not set.")
        return self._registry.has_component(self, component_type)

    def __repr__(self) -> str:
        return f"Entity(id={self._id})"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: "Entity") -> bool:
        if not isinstance(other, Entity):
            return False
        return self._id == other._id


@dataclass
class Registry:
    number_of_entities: int = 0
    component_pools: List[Optional[IComponentPool]] = field(default_factory=list)
    systems: Dict[str, Optional[System]] = field(default_factory=dict)
    entity_component_signatures: List[Signature] = field(default_factory=list)

    entities_to_be_added: List[Entity] = field(default_factory=list)
    entities_to_be_removed: List[Entity] = field(default_factory=list)

    def create_entity(self) -> Entity:
        self.number_of_entities += 1
        entity_id = self.number_of_entities
        if entity_id >= len(self.entity_component_signatures):
            # add a new signature for the new entity
            self.entity_component_signatures.extend([Signature(MAX_COMPONENTS)])

        entity = Entity(entity_id, self)
        self.entities_to_be_added.append(entity)
        return entity

    # Component management
    def add_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
        **kwargs,
    ) -> None:
        logger.debug(f"Adding component {component_type.__name__} to entity {entity}.")
        entity_id = entity.get_id()

        component_id = ComponentIndex.get_id(component_type.__name__)

        if component_id >= len(self.component_pools):
            if component_id >= MAX_COMPONENTS:
                # Raise an error if the maximum number of components is exceeded
                # TODO: Add a custom exception
                raise RuntimeError(
                    f"Maximum number of components ({MAX_COMPONENTS}) exceeded."
                )
            self.component_pools.extend(
                [None] * (component_id - len(self.component_pools) + 1)
            )
        if self.component_pools[component_id] is None:
            self.component_pools[component_id] = ComponentPool(component_type)

        component_pool = cast(
            ComponentPool[TComponent], self.component_pools[component_id]
        )
        component = component_type(**kwargs)
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
        if component_id > len(self.component_pools):
            return None
        if self.component_pools[component_id] is None:
            return None

        component_pool: ComponentPool[TComponent] = cast(
            ComponentPool[TComponent], self.component_pools[component_id]
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
    def add_system(self, system: Type[System], **kwargs) -> None:
        system_name: str = str(system.__name__)
        self.systems[system_name] = system(**kwargs)

    def add_entity_to_systems(self, entity: Entity) -> None:
        entity_id: int = entity.get_id()
        entity_component_signature: Signature = self.entity_component_signatures[
            entity_id - 1
        ]

        for system in self.systems.values():
            if system is None:
                continue

            if system.get_component_signature().matches(entity_component_signature):
                system.add_entity_to_system(entity)

    def remove_entity_from_systems(self, entity: Entity) -> None:
        for system in self.systems.values():
            if system is None:
                continue
            system.remove_entity_from_system(entity)

    def remove_system(self, system: Type[TSystem]) -> None:
        system_name = type(system).__name__
        self.systems.pop(system_name)

    def has_system(self, system: Type[TSystem]) -> bool:
        system_name = type(system).__name__
        return system_name in self.systems

    def get_system(self, system: Type[TSystem]) -> Optional[TSystem]:
        system_name: str = system.__name__
        return cast(Optional[TSystem], self.systems.get(system_name))

    # Update
    def update(self) -> None:
        if len(self.entities_to_be_added) > 0:
            for entity in self.entities_to_be_added:
                self.add_entity_to_systems(entity)
            self.entities_to_be_added.clear()

        if len(self.entities_to_be_removed) > 0:
            for entity in self.entities_to_be_removed:
                self.remove_entity_from_systems(entity)
            self.entities_to_be_removed.clear()
