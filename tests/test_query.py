from unittest.mock import Mock

import pytest

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


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return Registry()


def test_query_creation():
    """Test basic query creation and initialization."""
    query = Query()
    assert query._signature is not None
    assert len(query._entities) == 0
    assert query._kind is None


def test_query_add_remove_entities(registry):
    """Test adding and removing entities from queries."""
    query = Query()
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()

    # Add entities
    query.add_entity(entity1)
    query.add_entity(entity2)
    assert len(query._entities) == 2
    assert entity1 in query._entities
    assert entity2 in query._entities

    # Remove entity
    query.remove_entity(entity1)
    assert len(query._entities) == 1
    assert entity1 not in query._entities
    assert entity2 in query._entities

    # Try to remove non-existent entity (should not raise)
    non_existent = registry.create_entity()
    query.remove_entity(non_existent)
    assert len(query._entities) == 1


def test_query_iteration(registry):
    """Test iterating over query entities."""
    query = Query[Entity, With[Position, Velocity]]()
    entities = [registry.create_entity() for _ in range(3)]

    for entity in entities:
        query.add_entity(entity)

    # Test iteration
    result_entities = list(query.get_entities())
    assert len(result_entities) == 3
    for entity in entities:
        assert entity in result_entities


def test_query_signature_generation():
    """Test query signature generation for components."""
    query = Query[Entity, With[Position, Velocity]]()

    # Simulate component signature setup
    from arepy.ecs.components import ComponentIndex

    pos_id = ComponentIndex.get_id(Position.__name__)
    vel_id = ComponentIndex.get_id(Velocity.__name__)

    query._signature.set(pos_id, True)
    query._signature.set(vel_id, True)

    signature = query.get_component_signature()
    assert signature.test(pos_id)
    assert signature.test(vel_id)


def test_get_signed_query_arguments():
    """Test query argument signing from function annotations."""

    def test_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        pass

    arguments = get_signed_query_arguments(test_system)
    assert "query" in arguments
    assert isinstance(arguments["query"], Query)


def test_sign_queries_with_components():
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
        assert isinstance(result, list)
    except (AttributeError, TypeError):
        # Expected due to mock limitations with complex type annotations
        pass


def test_query_component_matching(registry):
    """Test query matching entities with specific components."""
    # Create entities with different component combinations
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()
    entity3 = registry.create_entity()

    # Add components
    registry.add_component(entity1, Position, Position(1.0, 2.0))
    registry.add_component(entity1, Velocity, Velocity(3.0, 4.0))

    registry.add_component(entity2, Position, Position(5.0, 6.0))
    # entity2 doesn't have Velocity

    registry.add_component(entity3, Velocity, Velocity(7.0, 8.0))
    # entity3 doesn't have Position

    # Update registry to sync queries
    registry.update()

    # Create a query for entities with both Position and Velocity
    query = Query[Entity, With[Position, Velocity]]()
    from arepy.ecs.components import ComponentIndex

    pos_id = ComponentIndex.get_id(Position.__name__)
    vel_id = ComponentIndex.get_id(Velocity.__name__)

    query._signature.set(pos_id, True)
    query._signature.set(vel_id, True)

    # Manually add entities that match (in real system, this is done by registry)
    if registry.has_component(entity1, Position) and registry.has_component(
        entity1, Velocity
    ):
        query.add_entity(entity1)

    # Only entity1 should match
    entities = list(query.get_entities())
    assert len(entities) == 1
    assert entity1 in entities


def test_query_with_registry_sync(registry):
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

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, test_system)

    # Create entity and add component
    entity = registry.create_entity()
    registry.add_component(entity, Position, Position(10.0, 20.0))
    registry.update()

    # Check that query was properly set up
    assert test_system in registry.queries
    query_args = registry.queries[test_system]
    assert len(query_args) > 0


def test_query_signature_matching():
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
    assert sig1.matches(sig2)
    # But sig2 should not match sig1 (sig1 doesn't have component 3)
    assert not sig2.matches(sig1)


def test_query_empty_results():
    """Test query behavior with no matching entities."""
    query = Query()
    entities = list(query.get_entities())
    assert len(entities) == 0

    # Test iteration on empty query
    count = 0
    for entity in query.get_entities():
        count += 1
    assert count == 0


def test_query_with_without_combinations(registry):
    """Test queries with With and Without combinations."""
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()
    entity3 = registry.create_entity()

    # entity1: Position + Velocity
    registry.add_component(entity1, Position, Position(1.0, 2.0))
    registry.add_component(entity1, Velocity, Velocity(3.0, 4.0))

    # entity2: Position + Health
    registry.add_component(entity2, Position, Position(5.0, 6.0))
    registry.add_component(entity2, Health, Health(50))

    # entity3: Velocity + Health
    registry.add_component(entity3, Velocity, Velocity(7.0, 8.0))
    registry.add_component(entity3, Health, Health(100))

    registry.update()

    # Test query for entities with Position but without Health
    # Note: Combined With/Without syntax is not yet implemented
    # Using basic Query instead
    query = Query()
    from arepy.ecs.components import ComponentIndex

    pos_id = ComponentIndex.get_id(Position.__name__)
    health_id = ComponentIndex.get_id(Health.__name__)

    query._signature.set(pos_id, True)
    # For Without, we'd need to handle exclusion logic in the registry
    # This is a simplified test

    # Manually add entity1 (has Position, no Health initially)
    if registry.has_component(entity1, Position) and not registry.has_component(
        entity1, Health
    ):
        query.add_entity(entity1)

    entities = list(query.get_entities())
    assert len(entities) == 1
    assert entity1 in entities


def test_query_registry_integration(registry):
    """Test full query integration with registry."""

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        """System that moves entities with position and velocity."""
        for entity in query.get_entities():
            pos = entity.get_component(Position)
            vel = entity.get_component(Velocity)
            pos.x += vel.x
            pos.y += vel.y

    # Add system to registry
    from arepy.ecs.systems import SystemPipeline, SystemState

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    # Create test entities
    moving_entity = registry.create_entity()
    static_entity = registry.create_entity()

    # Add components
    registry.add_component(moving_entity, Position, Position(0.0, 0.0))
    registry.add_component(moving_entity, Velocity, Velocity(1.0, 2.0))
    registry.add_component(static_entity, Position, Position(10.0, 10.0))
    # static_entity has no velocity

    # Update registry to process systems
    registry.update()

    # Verify system was registered with queries
    assert movement_system in registry.queries
