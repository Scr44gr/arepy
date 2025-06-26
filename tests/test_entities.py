import pytest

from arepy.ecs.components import Component
from arepy.ecs.entities import Entity
from arepy.ecs.exceptions import ComponentNotFoundError, RegistryNotSetError
from arepy.ecs.registry import Registry


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


class Health(Component):
    def __init__(self, value: int = 100):
        super().__init__()
        self.value = value


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return Registry()


@pytest.fixture
def entity(registry):
    """Create an entity for testing."""
    return registry.create_entity()


def test_entity_creation(registry):
    """Test entity creation and basic properties."""
    entity = registry.create_entity()
    assert entity.get_id() == 1
    assert isinstance(entity.get_id(), int)
    assert entity._registry is registry


def test_entity_id_assignment(registry):
    """Test that entities get sequential IDs."""
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()
    entity3 = registry.create_entity()

    assert entity1.get_id() == 1
    assert entity2.get_id() == 2
    assert entity3.get_id() == 3


def test_entity_component_operations(entity):
    """Test adding, getting, and removing components."""
    pos = Position(10.0, 20.0)
    vel = Velocity(5.0, 3.0)

    # Add components
    entity.add_component(pos)
    entity.add_component(vel)

    # Check if entity has components
    assert entity.has_component(Position)
    assert entity.has_component(Velocity)
    assert not entity.has_component(Health)

    # Get components
    retrieved_pos = entity.get_component(Position)
    retrieved_vel = entity.get_component(Velocity)

    assert retrieved_pos.x == 10.0
    assert retrieved_pos.y == 20.0
    assert retrieved_vel.x == 5.0
    assert retrieved_vel.y == 3.0

    # Remove component
    entity.remove_component(Position)
    assert not entity.has_component(Position)
    assert entity.has_component(Velocity)


def test_entity_component_cache(entity):
    """Test that component cache works correctly."""
    pos = Position(15.0, 25.0)
    entity.add_component(pos)

    # First access should cache the component
    component1 = entity.get_component(Position)
    component2 = entity.get_component(Position)

    # Should return the same object from cache
    assert component1 is component2
    assert component1.x == 15.0


def test_entity_component_not_found(entity):
    """Test ComponentNotFoundError when getting non-existent component."""
    with pytest.raises(ComponentNotFoundError):
        entity.get_component(Position)


def test_entity_add_duplicate_component(entity):
    """Test that adding duplicate components doesn't cause issues."""
    pos1 = Position(1.0, 2.0)
    pos2 = Position(3.0, 4.0)

    entity.add_component(pos1)
    entity.add_component(pos2)  # Should replace or handle gracefully

    # Should have the component
    assert entity.has_component(Position)


def test_entity_equality(registry):
    """Test entity equality and hash functionality."""
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()
    entity3 = Entity(entity1.get_id(), registry)  # Same ID

    # Entities with same ID should be equal
    assert entity1 == entity3
    assert entity1 != entity2

    # Test hash consistency
    assert hash(entity1) == hash(entity3)
    assert hash(entity1) != hash(entity2)


def test_entity_string_representation(entity):
    """Test entity string representation."""
    entity_str = str(entity)
    entity_repr = repr(entity)

    assert f"Entity(id={entity.get_id()})" == entity_str
    assert entity_str == entity_repr


def test_entity_kill(entity):
    """Test entity killing functionality."""
    pos = Position(1.0, 2.0)
    entity.add_component(pos)

    # Entity should have component before killing
    assert entity.has_component(Position)

    # Kill entity
    entity.kill()

    # Component cache should be cleared
    assert len(entity._component_cache) == 0


def test_entity_without_registry():
    """Test entity operations without registry should raise RegistryNotSetError."""
    entity = Entity(1, None)  # type: ignore

    with pytest.raises(RegistryNotSetError):
        entity.get_component(Position)

    with pytest.raises(RegistryNotSetError):
        entity.has_component(Position)

    with pytest.raises(RegistryNotSetError):
        entity.add_component(Position(1.0, 2.0))

    with pytest.raises(RegistryNotSetError):
        entity.remove_component(Position)

    with pytest.raises(RegistryNotSetError):
        entity.kill()


def test_entity_component_cache_invalidation(entity):
    """Test that removing components invalidates cache."""
    pos = Position(10.0, 20.0)
    entity.add_component(pos)

    # Access component to cache it
    cached_pos = entity.get_component(Position)
    assert Position in entity._component_cache

    # Remove component
    entity.remove_component(Position)

    # Cache should be invalidated
    assert Position not in entity._component_cache


def test_entity_in_set_and_dict(registry):
    """Test that entities work correctly in sets and dictionaries."""
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()
    entity3 = Entity(entity1.get_id(), registry)  # Same ID as entity1

    # Test in set
    entity_set = {entity1, entity2, entity3}
    assert len(entity_set) == 2  # entity1 and entity3 should be treated as same

    # Test as dictionary key
    entity_dict = {entity1: "first", entity2: "second"}
    assert entity_dict[entity3] == "first"  # entity3 has same ID as entity1
