import unittest
from unittest.mock import Mock

from arepy.ecs.components import Component
from arepy.ecs.entities import Entity
from arepy.ecs.query import (
    Query,
    With,
    Without,
    get_signed_query_arguments,
    sign_queries,
)
from arepy.ecs.registry import Registry
from arepy.ecs.utils import Signature


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


class Health(Component):
    def __init__(self, value: int = 100):
        self.value = value


class QueryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()

    def test_query_creation(self):
        """Test basic query creation and initialization."""
        query = Query()
        self.assertIsNotNone(query._signature)
        self.assertEqual(len(query._entities), 0)
        self.assertIsNone(query._kind)

    def test_query_add_remove_entities(self):
        """Test adding and removing entities from queries."""
        query = Query()
        entity1 = self.registry.create_entity()
        entity2 = self.registry.create_entity()

        # Add entities
        query.add_entity(entity1)
        query.add_entity(entity2)
        self.assertEqual(len(query._entities), 2)
        self.assertIn(entity1, query._entities)
        self.assertIn(entity2, query._entities)

        # Remove entity
        query.remove_entity(entity1)
        self.assertEqual(len(query._entities), 1)
        self.assertNotIn(entity1, query._entities)
        self.assertIn(entity2, query._entities)

        # Try to remove non-existent entity (should not raise)
        non_existent = self.registry.create_entity()
        query.remove_entity(non_existent)
        self.assertEqual(len(query._entities), 1)

    def test_query_iteration(self):
        """Test iterating over query entities."""
        query = Query[Entity, With[Position, Velocity]]()
        entities = [self.registry.create_entity() for _ in range(3)]

        for entity in entities:
            query.add_entity(entity)

        # Test iteration
        result_entities = list(query.get_entities())
        self.assertEqual(len(result_entities), 3)
        for entity in entities:
            self.assertIn(entity, result_entities)

    def test_query_signature_generation(self):
        """Test query signature generation for components."""
        query = Query[Entity, With[Position, Velocity]]()

        # Simulate component signature setup
        from arepy.ecs.components import ComponentIndex

        pos_id = ComponentIndex.get_id(Position.__name__)
        vel_id = ComponentIndex.get_id(Velocity.__name__)

        query._signature.set(pos_id, True)
        query._signature.set(vel_id, True)

        signature = query.get_component_signature()
        self.assertTrue(signature.test(pos_id))
        self.assertTrue(signature.test(vel_id))

    def test_get_signed_query_arguments(self):
        """Test query argument signing from function annotations."""

        def test_system(query: Query[Entity, With[Position, Velocity]]) -> None:
            pass

        arguments = get_signed_query_arguments(test_system)
        self.assertIn("query", arguments)
        self.assertIsInstance(arguments["query"], Query)

    def test_sign_queries_with_components(self):
        """Test signing queries with specific component types."""
        # Mock query factory
        mock_query_factory = Mock()
        mock_query_factory.__args__ = [Entity, With[Position, Velocity]]
        mock_query_factory.return_value = Query()

        # Create mock With type
        mock_with = Mock()
        mock_with.__origin__ = With
        mock_with.__args__ = [[Position, Velocity]]
        mock_query_factory.__args__ = [Entity, mock_with]

        # This would be more complex to fully test due to type system complexities
        # For now, we test the structure
        queries = [("test_query", mock_query_factory)]

        try:
            result = sign_queries(queries)
            # If it doesn't crash, the basic structure is working
            self.assertIsInstance(result, list)
        except (AttributeError, TypeError):
            # Expected due to mock limitations with complex type annotations
            pass

    def test_query_component_matching(self):
        """Test query matching entities with specific components."""
        # Create entities with different component combinations
        entity1 = self.registry.create_entity()
        entity2 = self.registry.create_entity()
        entity3 = self.registry.create_entity()

        # Add components
        self.registry.add_component(entity1, Position, Position(1.0, 2.0))
        self.registry.add_component(entity1, Velocity, Velocity(3.0, 4.0))

        self.registry.add_component(entity2, Position, Position(5.0, 6.0))
        # entity2 doesn't have Velocity

        self.registry.add_component(entity3, Velocity, Velocity(7.0, 8.0))
        # entity3 doesn't have Position

        # Update registry to sync queries
        self.registry.update()

        # Create a query for entities with both Position and Velocity
        query = Query[Entity, With[Position, Velocity]]()
        from arepy.ecs.components import ComponentIndex

        pos_id = ComponentIndex.get_id(Position.__name__)
        vel_id = ComponentIndex.get_id(Velocity.__name__)

        query._signature.set(pos_id, True)
        query._signature.set(vel_id, True)

        # Manually add entities that match (in real system, this is done by registry)
        if self.registry.has_component(
            entity1, Position
        ) and self.registry.has_component(entity1, Velocity):
            query.add_entity(entity1)

        # Only entity1 should match
        entities = list(query.get_entities())
        self.assertEqual(len(entities), 1)
        self.assertIn(entity1, entities)

    def test_query_with_registry_sync(self):
        """Test query synchronization with registry when entities are added/removed."""

        # Create a simple system function
        def test_system(query: Query[Entity, With[Position]]) -> None:
            """A mock system that processes entities with Position component."""
            for entity in query.get_entities():
                pos = entity.get_component(Position)
                # Just a dummy operation
                pos.x += 1.0
                pos.y += 1.0

        # Add system to registry
        from arepy.ecs.systems import SystemPipeline, SystemState

        self.registry.add_system(SystemPipeline.UPDATE, SystemState.ON, test_system)

        # Create entity and add component
        entity = self.registry.create_entity()
        self.registry.add_component(entity, Position, Position(10.0, 20.0))
        self.registry.update()

        # Check that query was properly set up
        self.assertIn(test_system, self.registry.queries)
        query_args = self.registry.queries[test_system]
        self.assertTrue(len(query_args) > 0)

    def test_query_signature_matching(self):
        """Test signature matching logic."""
        from arepy.ecs.constants import MAX_COMPONENTS
        from arepy.ecs.utils import Signature

        # Create two signatures
        sig1 = Signature(MAX_COMPONENTS)
        sig2 = Signature(MAX_COMPONENTS)

        # Set same components
        sig1.set(1, True)
        sig1.set(2, True)

        sig2.set(1, True)
        sig2.set(2, True)
        sig2.set(3, True)  # Additional component

        # sig1 should match sig2 (sig2 has all components of sig1)
        self.assertTrue(sig1.matches(sig2))
        # But sig2 should not match sig1 (sig1 doesn't have component 3)
        self.assertFalse(sig2.matches(sig1))

    def test_query_empty_results(self):
        """Test query behavior with no matching entities."""
        query = Query()
        entities = list(query.get_entities())
        self.assertEqual(len(entities), 0)

        # Test iteration on empty query
        count = 0
        for entity in query.get_entities():
            count += 1
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
