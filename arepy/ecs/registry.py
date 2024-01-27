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

    def get_component(self, component_type: Type[TComponent]) -> Optional[TComponent]:
        if self._registry is None:
            raise RuntimeError("Registry is not set.")
        return self._registry.get_component(self, component_type)

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
        if component_id > len(self.component_pools):
            if component_id >= MAX_COMPONENTS:
                # Raise an error if the maximum number of components is exceeded
                # TODO: Add a custom exception
                raise RuntimeError(
                    f"Maximum number of components ({MAX_COMPONENTS}) exceeded."
                )
            self.component_pools.extend([None] * (component_id + 1))
        if self.component_pools[component_id - 1] is None:
            self.component_pools[component_id - 1] = ComponentPool(component_type)

        component_pool = cast(
            ComponentPool[TComponent], self.component_pools[component_id - 1]
        )
        component = component_type(**kwargs)

        # Resize the component pool if necessary
        if entity_id >= len(component_pool):
            component_pool.extend([None] * (self.number_of_entities + 1))
        # Set the component to the pool
        component_pool.set(entity_id, component)

        # Extend the entity component signatures if necessary
        if component_id > len(self.entity_component_signatures):
            self.entity_component_signatures.extend(
                [Signature(MAX_COMPONENTS)] * (component_id + 1)
            )
        # Set the component signature
        self.entity_component_signatures[entity_id].set(component_id, True)

    def get_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> Optional[TComponent]:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)
        if component_id > len(self.component_pools):
            return None
        if self.component_pools[component_id - 1] is None:
            return None

        component_pool: ComponentPool[TComponent] = cast(
            ComponentPool[TComponent], self.component_pools[component_id - 1]
        )
        if entity_id > len(component_pool):
            return None

        return component_pool.get(entity_id)

    def remove_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> None:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)
        self.entity_component_signatures[entity_id].clear_bit(component_id)

    def has_component(
        self,
        entity: Entity,
        component_type: Type[TComponent],
    ) -> bool:
        entity_id: int = entity.get_id()
        component_id: int = ComponentIndex.get_id(component_type.__name__)

        return self.entity_component_signatures[entity_id].test(component_id)

    # System management
    def add_system(self, system: Type[TSystem], **kwargs) -> None:
        system_name: str = type(system).__name__
        self.systems[system_name] = system(**kwargs)

    def add_entity_to_systems(self, entity: Entity) -> None:
        entity_id: int = entity.get_id()

        for system in self.systems.values():
            if system is None:
                continue
            if not system.get_component_signature().matches(
                self.entity_component_signatures[entity_id]
            ):
                continue
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
        system_name = type(system).__name__
        return cast(Optional[TSystem], self.systems.get(system_name))

    # Update
    def update(self) -> None:
        for entity in self.entities_to_be_added:
            self.add_entity_to_systems(entity)
        for entity in self.entities_to_be_removed:
            self.remove_entity_from_systems(entity)

        self.entities_to_be_added.clear()
        self.entities_to_be_removed.clear()
