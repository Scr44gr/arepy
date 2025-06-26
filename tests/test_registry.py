from unittest import TestCase
from unittest.mock import patch

from arepy.ecs.components import Component
from arepy.ecs.registry import Registry


class Position(Component):
    x: int
    y: int


class Velocity(Component):
    x: int
    y: int


class RegistryTest(TestCase):
    def setUp(self) -> None:
        self.registry = Registry()

    def test_create_entity(self):
        entity = self.registry.create_entity()
        self.assertEqual(entity.get_id(), 1)

    def test_add_and_remove_components(self):
        # Add and entity
        entity = self.registry.create_entity()

        # Add components to the entity
        self.registry.add_component(entity, Position, Position(x=0, y=0))
        self.registry.add_component(entity, Velocity, Velocity(x=1, y=1))

        # Ensure that the entity has the components
        self.assertEqual(self.registry.number_of_entities, 1)
        self.assertEqual(len(self.registry.component_pools), 3)
        self.assertEqual(len(self.registry.entity_component_signatures), 1)
        self.assertEqual(len(self.registry.entities_to_be_added), 1)
        self.assertEqual(len(self.registry.entities_to_be_removed), 0)

        # Remove the component from the entity
        self.registry.remove_component(entity, Position)

        # Ensure the component is removed
        self.assertFalse(self.registry.has_component(entity, Position))
        self.assertTrue(self.registry.has_component(entity, Velocity))

    def test_kill_entities(self):
        # Add and entity
        registry = Registry()
        entity = registry.create_entity()

        # Add components to the entity
        registry.add_component(entity, Position, Position(x=0, y=0))
        registry.add_component(entity, Velocity, Velocity(x=1, y=1))

        # Kill the entity
        registry.kill_entity(entity)
        self.assertEqual(len(registry.entities_to_be_removed), 1)
        # Update the registry
        registry.update()
        # Ensure the entity is removed
        self.assertEqual(registry.number_of_entities, 1)

        # new_pool_size = max(entity_id + 1, len(component_pool) * 2)

        self.assertEqual(len(registry.component_pools), 3)  # + 1 None
        self.assertEqual(len(registry.entity_component_signatures), 1)
        self.assertEqual(len(registry.entities_to_be_removed), 0)


# to run: python -m unittest tests/test_registry.py
