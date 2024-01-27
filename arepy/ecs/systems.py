from typing import List, Type, TypeVar

from arepy.ecs.constants import MAX_COMPONENTS

from .components import ComponentIndex, TComponent

try:
    from .registry import Entity
except ImportError:
    ...
from .utils import Signature

TSystem = TypeVar("TSystem", bound="System")


class System:
    """Base class for all systems."""

    entity_component_signature: Signature = Signature(MAX_COMPONENTS)
    entities: List["Entity"] = list()

    def add_entity_to_system(self, entity: "Entity") -> None:
        """Add an entity to the system.

        Args:
            entity: The entity to add.
        """
        self.entities.append(entity)

    def require_component(self, component_type: Type[TComponent]) -> None:
        """Require a component type for the system.

        Args:
            component_type: The component type to require.
        """
        component_id = ComponentIndex.get_id(component_type.__name__)
        self.entity_component_signature.set(component_id, True)

    def get_component_signature(self) -> Signature:
        """Get the component signature of the system.

        Returns:
            The component signature of the system.
        """
        return self.entity_component_signature

    def remove_entity_from_system(self, entity: "Entity") -> None:
        """Remove an entity from the system.

        Args:
            entity: The entity to remove.
        """
        for i, system_entity in enumerate(self.entities):
            if system_entity == entity:
                self.entities.pop(i)
                break

    def update(self, *args, **kwargs) -> None:
        """Update the system."""
        raise NotImplementedError
