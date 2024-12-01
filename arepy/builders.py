from typing import List

from .ecs.components import Component
from .ecs.registry import Entity, Registry


class EntityBuilder:
    """A builder for entities.

    This is a wrapped class for the entity class.
    It allows for the creation of entities with components without having to touch the ecs registry.
    """

    _registry: Registry

    def __init__(self, entity: Entity, registry: Registry):
        self._entity = entity
        self._components: List[Component] = list()
        self._registry = registry

    def with_component(self, component: Component) -> "EntityBuilder":
        """Add a component to the entity.

        Returns:
            A component builder.
        """
        if not isinstance(component, Component):
            raise TypeError(
                f"Component must be of type Component, not {type(component)}."
            )

        for _component in self._components:
            if type(_component) == type(component):
                raise TypeError(
                    f"Component {type(component)} already exists in entity."
                )

        self._components.append(component)
        return self

    def build(self) -> Entity:
        """Build the entity with the components, the components are built and added to the registry."""
        for component in self._components:
            self._registry.add_component(
                self._entity,
                type(component),
                component,
            )

        return self._entity
