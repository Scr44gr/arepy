import pytest

from arepy.ecs.components import Component
from arepy.ecs.registry import Registry


class Position(Component):
    def __init__(self, x: int = 0, y: int = 0):
        super().__init__()
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x: int = 0, y: int = 0):
        super().__init__()
        self.x = x
        self.y = y


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return Registry()


def test_create_entity(registry):
    """Test entity creation and ID assignment."""
    entity = registry.create_entity()
    assert entity.get_id() == 1


def test_add_and_remove_components(registry):
    """Test adding and removing components from entities."""
    # Add an entity
    entity = registry.create_entity()

    # Add components to the entity
    registry.add_component(entity, Position, Position(x=0, y=0))
    registry.add_component(entity, Velocity, Velocity(x=1, y=1))

    # Ensure that the entity has the components
    assert registry.number_of_entities == 1
    assert len(registry.component_pools) == 3
    assert len(registry.entity_component_signatures) == 1
    assert len(registry.entities_to_be_added) == 1
    assert len(registry.entities_to_be_removed) == 0

    # Remove the component from the entity
    registry.remove_component(entity, Position)

    # Ensure the component is removed
    assert not registry.has_component(entity, Position)
    assert registry.has_component(entity, Velocity)


def test_kill_entities():
    """Test entity killing and cleanup."""
    # Add an entity
    registry = Registry()
    entity = registry.create_entity()

    # Add components to the entity
    registry.add_component(entity, Position, Position(x=0, y=0))
    registry.add_component(entity, Velocity, Velocity(x=1, y=1))

    # Kill the entity
    registry.kill_entity(entity)
    assert len(registry.entities_to_be_removed) == 1

    # Update the registry
    registry.update()

    # Ensure the entity is removed
    assert registry.number_of_entities == 1
    # new_pool_size = max(entity_id + 1, len(component_pool) * 2)
    assert len(registry.component_pools) == 3  # + 1 None
    assert len(registry.entity_component_signatures) == 1
    assert len(registry.entities_to_be_removed) == 0


def test_multiple_entities(registry):
    """Test creating and managing multiple entities."""
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()
    entity3 = registry.create_entity()

    assert entity1.get_id() == 1
    assert entity2.get_id() == 2
    assert entity3.get_id() == 3
    assert registry.number_of_entities == 3


def test_component_retrieval(registry):
    """Test retrieving components from entities."""
    entity = registry.create_entity()
    pos = Position(x=10, y=20)
    vel = Velocity(x=5, y=15)

    registry.add_component(entity, Position, pos)
    registry.add_component(entity, Velocity, vel)

    # Retrieve components
    retrieved_pos = registry.get_component(entity, Position)
    retrieved_vel = registry.get_component(entity, Velocity)

    assert retrieved_pos is not None
    assert retrieved_vel is not None
    assert retrieved_pos.x == 10
    assert retrieved_pos.y == 20
    assert retrieved_vel.x == 5
    assert retrieved_vel.y == 15


def test_registry_update_cycle(registry):
    """Test the registry update cycle with pending entities."""
    # Create entities but don't update yet
    entity1 = registry.create_entity()
    entity2 = registry.create_entity()

    registry.add_component(entity1, Position, Position(x=1, y=1))
    registry.add_component(entity2, Position, Position(x=2, y=2))

    # Before update, entities should be pending
    assert len(registry.entities_to_be_added) == 2

    # Update registry
    registry.update()

    # After update, no more pending entities
    assert len(registry.entities_to_be_added) == 0


def test_entity_signature_management(registry):
    """Test entity signature management."""
    entity = registry.create_entity()

    # Add components and check signature changes
    registry.add_component(entity, Position, Position(x=0, y=0))

    # Entity should have a signature
    assert entity.get_id() == len(registry.entity_component_signatures)

    signature = registry.entity_component_signatures[entity.get_id() - 1]
    from arepy.ecs.components import ComponentIndex

    pos_id = ComponentIndex.get_id(Position.__name__)

    # Signature should have Position component set
    assert signature.test(pos_id)


# to run: pytest tests/test_registry.py
