from typing import Generic, List, Type, TypeVar, cast

from .ecs.components import Component, PComponent, TComponent
from .ecs.registry import Entity, Registry


class EntityBuilder:
    """A builder for entities.

    This class is used to build entities with components.
    """

    _registry: Registry
    _entity: Entity

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
        for component in self._components:
            component_args = component.__dict__.copy()
            self._registry.add_component(
                self._entity, type(component), **component_args
            )

        return self._entity
