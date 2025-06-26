import pytest

from arepy.ecs.builders import EntityBuilder
from arepy.ecs.components import Component
from arepy.ecs.entities import Entity
from arepy.ecs.registry import Registry
from arepy.ecs.systems import SystemPipeline, SystemState
from arepy.ecs.world import World


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


class TestWorld:
    def test_world_creation(self):
        """Test world creation and basic properties."""
        world = World("test_world")
        assert world.name == "test_world"
        assert isinstance(world._registry, Registry)

    def test_world_create_entity(self):
        """Test creating entities through world."""
        world = World("test_world")
        entity_builder = world.create_entity()

        assert isinstance(entity_builder, EntityBuilder)
        assert isinstance(entity_builder._entity, Entity)
        assert entity_builder._registry is world._registry

    def test_world_add_system(self):
        """Test adding systems to world."""
        world = World("test_world")

        def test_system():
            pass

        world.add_system(SystemPipeline.UPDATE, test_system)

        # Check that system was added to registry
        registry = world.get_registry()
        assert test_system in registry.systems[SystemPipeline.UPDATE][SystemState.ON]

    def test_world_add_multiple_systems(self):
        """Test adding multiple systems at once."""
        world = World("test_world")

        def system1():
            pass

        def system2():
            pass

        systems = {system1, system2}
        world.add_systems(SystemPipeline.UPDATE, systems)

        registry = world.get_registry()
        update_systems = registry.systems[SystemPipeline.UPDATE][SystemState.ON]
        assert system1 in update_systems
        assert system2 in update_systems

    def test_world_add_system_with_state(self):
        """Test adding system with specific state."""
        world = World("test_world")

        def test_system():
            pass

        world.add_system_with_state(SystemPipeline.RENDER, test_system, SystemState.OFF)

        registry = world.get_registry()
        assert test_system in registry.systems[SystemPipeline.RENDER][SystemState.OFF]
        assert (
            test_system not in registry.systems[SystemPipeline.RENDER][SystemState.ON]
        )

    def test_world_set_system_state(self):
        """Test changing system state."""
        world = World("test_world")

        def test_system():
            pass

        # Add system in ON state
        world.add_system(SystemPipeline.UPDATE, test_system)

        # Change to OFF state
        world.set_system_state(SystemPipeline.UPDATE, test_system, SystemState.OFF)

        registry = world.get_registry()
        assert (
            test_system not in registry.systems[SystemPipeline.UPDATE][SystemState.ON]
        )
        assert test_system in registry.systems[SystemPipeline.UPDATE][SystemState.OFF]

    def test_world_get_registry(self):
        """Test getting registry from world."""
        world = World("test_world")
        registry = world.get_registry()

        assert isinstance(registry, Registry)
        assert registry is world._registry


class TestEntityBuilder:
    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return Registry()

    @pytest.fixture
    def entity_builder(self, registry):
        """Create an entity builder for testing."""
        entity = registry.create_entity()
        return EntityBuilder(entity, registry)

    def test_entity_builder_creation(self, registry):
        """Test entity builder creation."""
        entity = registry.create_entity()
        builder = EntityBuilder(entity, registry)

        assert builder._entity is entity
        assert builder._registry is registry
        assert len(builder._components) == 0

    def test_entity_builder_with_component(self, entity_builder):
        """Test adding components to entity builder."""
        pos = Position(10.0, 20.0)
        vel = Velocity(5.0, 3.0)

        builder = entity_builder.with_component(pos).with_component(vel)

        assert len(builder._components) == 2
        assert pos in builder._components
        assert vel in builder._components
        assert builder is entity_builder  # Should return self for chaining

    def test_entity_builder_invalid_component(self, entity_builder):
        """Test adding invalid component raises TypeError."""
        with pytest.raises(TypeError, match="Component must be of type Component"):
            entity_builder.with_component("not_a_component")

    def test_entity_builder_duplicate_component(self, entity_builder):
        """Test adding duplicate component type raises TypeError."""
        pos1 = Position(1.0, 2.0)
        pos2 = Position(3.0, 4.0)

        entity_builder.with_component(pos1)

        with pytest.raises(TypeError, match="Component .* already exists in entity"):
            entity_builder.with_component(pos2)

    def test_entity_builder_build(self, entity_builder):
        """Test building entity with components."""
        pos = Position(15.0, 25.0)
        vel = Velocity(7.0, 9.0)
        health = Health(150)

        built_entity = (
            entity_builder.with_component(pos)
            .with_component(vel)
            .with_component(health)
            .build()
        )

        assert built_entity is entity_builder._entity

        # Verify components were added to registry
        registry = entity_builder._registry
        assert registry.has_component(built_entity, Position)
        assert registry.has_component(built_entity, Velocity)
        assert registry.has_component(built_entity, Health)

        # Verify component values
        retrieved_pos = registry.get_component(built_entity, Position)
        retrieved_vel = registry.get_component(built_entity, Velocity)
        retrieved_health = registry.get_component(built_entity, Health)

        assert retrieved_pos is not None
        assert retrieved_vel is not None
        assert retrieved_health is not None
        assert retrieved_pos.x == 15.0
        assert retrieved_pos.y == 25.0
        assert retrieved_vel.x == 7.0
        assert retrieved_vel.y == 9.0
        assert retrieved_health.value == 150

    def test_entity_builder_empty_build(self, entity_builder):
        """Test building entity without components."""
        built_entity = entity_builder.build()

        assert built_entity is entity_builder._entity
        assert len(entity_builder._components) == 0

    def test_entity_builder_fluent_interface(self, registry):
        """Test entity builder fluent interface."""
        entity = registry.create_entity()

        # Should be able to chain calls
        built_entity = (
            EntityBuilder(entity, registry)
            .with_component(Position(1.0, 2.0))
            .with_component(Velocity(3.0, 4.0))
            .with_component(Health(75))
            .build()
        )

        assert built_entity is entity
        assert registry.has_component(entity, Position)
        assert registry.has_component(entity, Velocity)
        assert registry.has_component(entity, Health)

    def test_world_entity_builder_integration(self):
        """Test world and entity builder integration."""
        world = World("integration_test")

        # Create entity through world and add components
        entity = (
            world.create_entity()
            .with_component(Position(100.0, 200.0))
            .with_component(Velocity(10.0, 20.0))
            .build()
        )

        # Verify entity exists in world's registry
        registry = world.get_registry()
        assert registry.has_component(entity, Position)
        assert registry.has_component(entity, Velocity)

        pos = registry.get_component(entity, Position)
        vel = registry.get_component(entity, Velocity)

        assert pos is not None
        assert vel is not None
        assert pos.x == 100.0
        assert pos.y == 200.0
        assert vel.x == 10.0
        assert vel.y == 20.0
