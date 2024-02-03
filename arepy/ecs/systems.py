import logging
from typing import List, Type, TypeVar

from arepy.ecs.constants import MAX_COMPONENTS

from .components import ComponentIndex, TComponent

try:
    from .registry import Entity
except ImportError:
    ...
from .utils import Signature

TSystem = TypeVar("TSystem", bound="System")
logger = logging.getLogger(__name__)


class System:
    """Base class for all systems."""

    def __init__(self) -> None:
        self.entity_component_signature = Signature(MAX_COMPONENTS)
        self.entities: List["Entity"] = list()

    def require_components(self, component_types: List[Type[TComponent]]) -> None:
        """Require components for the system.

        Args:
            component_types: The component types to require.
        """
        for component_type in component_types:
            component_id = ComponentIndex.get_id(component_type.__name__)
            self.entity_component_signature.set(component_id, True)

    def get_entities(self) -> List["Entity"]:
        """Get the entities of the system.

        Returns:
            The entities of the current system.
        """
        return self.entities

    def get_component_signature(self) -> Signature:
        """Get the component signature of the system.

        Returns:
            The component signature of the system.
        """
        return self.entity_component_signature

    def _remove_entity(self, entity: "Entity") -> None:
        """Remove an entity from the system.

        Args:
            entity: The entity to remove.
        """
        if entity in self.entities:
            self.entities.remove(entity)
            return
        logger.warning(f"Entity {entity} not found in system {self}.")

    def _add_entity(self, entity: "Entity") -> None:
        """Add an entity to the current system.

        Args:
            entity: The entity to add.
        """
        self.entities.append(entity)

    def update(self, *args, **kwargs) -> None:
        """Update the system."""
        raise NotImplementedError
