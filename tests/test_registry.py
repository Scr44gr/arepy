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


class MockRenderer:
    def __init__(self, name: str = "default"):
        self.name = name
        self.draw_count = 0

    def draw(self) -> None:
        self.draw_count += 1


class MockInput:
    def __init__(self):
        self.keys_pressed: list[str] = []

    def is_key_pressed(self, key: str) -> bool:
        return key in self.keys_pressed


class TestResourceInjection:

    def test_resource_injection_basic(self):
        registry = Registry()
        renderer = MockRenderer("test_renderer")
        registry.resources["MockRenderer"] = renderer

        call_count = 0

        def render_system(r: MockRenderer) -> None:
            nonlocal call_count
            call_count += 1
            r.draw()

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(SystemPipeline.RENDER, SystemState.ON, render_system)
        registry.run(SystemPipeline.RENDER)

        assert call_count == 1
        assert renderer.draw_count == 1

    def test_resource_injection_multiple_resources(self):
        registry = Registry()
        renderer = MockRenderer("multi_test")
        input_device = MockInput()
        registry.resources["MockRenderer"] = renderer
        registry.resources["MockInput"] = input_device

        received_resources: list[object] = []

        def system_with_multiple_resources(r: MockRenderer, i: MockInput) -> None:
            received_resources.append(r)
            received_resources.append(i)

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(
            SystemPipeline.UPDATE, SystemState.ON, system_with_multiple_resources
        )
        registry.run(SystemPipeline.UPDATE)

        assert len(received_resources) == 2
        assert received_resources[0] is renderer
        assert received_resources[1] is input_device

    def test_resource_lazy_resolution(self):
        registry = Registry()
        renderer = MockRenderer("initial")
        registry.resources["MockRenderer"] = renderer

        received_renderers: list[MockRenderer] = []

        def capture_renderer(r: MockRenderer) -> None:
            received_renderers.append(r)

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_renderer)

        registry.run(SystemPipeline.UPDATE)
        assert received_renderers[0] is renderer

        new_renderer = MockRenderer("replaced")
        registry.resources["MockRenderer"] = new_renderer

        registry.run(SystemPipeline.UPDATE)
        assert received_renderers[1] is new_renderer

    def test_resource_added_after_system_registration(self):
        registry = Registry()
        registry.resources["MockRenderer"] = MockRenderer("placeholder")

        received_input: list[MockInput] = []

        def system_needing_input(i: MockInput) -> None:
            received_input.append(i)

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.resources["MockInput"] = MockInput()
        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, system_needing_input)

        late_input = MockInput()
        late_input.keys_pressed = ["W", "A", "S", "D"]
        registry.resources["MockInput"] = late_input

        registry.run(SystemPipeline.UPDATE)

        assert len(received_input) == 1
        assert received_input[0] is late_input

    def test_world_resources_override_global_resources(self):
        registry = Registry()
        global_renderer = MockRenderer("global")
        world_renderer = MockRenderer("world")
        registry.global_resources["MockRenderer"] = global_renderer
        registry.resources["MockRenderer"] = world_renderer

        received_renderers: list[MockRenderer] = []

        def capture_renderer(r: MockRenderer) -> None:
            received_renderers.append(r)

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_renderer)
        registry.run(SystemPipeline.UPDATE)

        assert received_renderers == [world_renderer]

    def test_resource_marker_survives_late_resource_registration(self):
        registry = Registry()

        received_renderers: list[object] = []

        def capture_renderer(r: MockRenderer) -> None:
            received_renderers.append(r)

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_renderer)

        late_renderer = MockRenderer("late")
        registry.resources["MockRenderer"] = late_renderer
        registry.run(SystemPipeline.UPDATE)

        assert received_renderers == [late_renderer]

    def test_resource_markers_created_correctly(self):
        registry = Registry()
        renderer = MockRenderer()
        registry.resources["MockRenderer"] = renderer

        def system_with_resource(r: MockRenderer) -> None:
            pass

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, system_with_resource)

        assert system_with_resource in registry.resource_markers
        markers = registry.resource_markers[system_with_resource]
        assert len(markers) == 1
        assert markers[0].name == "MockRenderer"
        assert markers[0].index == 0

    def test_resource_with_query_arguments(self):
        registry = Registry()
        renderer = MockRenderer()
        registry.resources["MockRenderer"] = renderer

        from arepy.ecs.entities import Entity
        from arepy.ecs.query import Query, With

        entities_processed: list[int] = []
        renderer_received: list[MockRenderer] = []

        def mixed_system(r: MockRenderer, q: Query[Entity, With[Position]]) -> None:
            renderer_received.append(r)
            for entity in q.get_entities():
                entities_processed.append(entity.get_id())

        from arepy.ecs.systems import SystemPipeline, SystemState

        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, mixed_system)

        entity = registry.create_entity()
        registry.add_component(entity, Position, Position(10, 20))
        registry.update()

        registry.run(SystemPipeline.UPDATE)

        assert len(renderer_received) == 1
        assert renderer_received[0] is renderer
        assert len(entities_processed) == 1
        assert entities_processed[0] == entity.get_id()


def test_kill_clears_component_slots_and_reuses_pool_capacity() -> None:
    registry = Registry()
    entity = registry.create_entity()
    original = Position(1, 2)
    registry.add_component(entity, Position, original)
    registry.update()

    from arepy.ecs.components import ComponentIndex

    component_id = ComponentIndex.get_type_id(Position)
    pool = registry.component_pools[component_id - 1]
    assert pool is not None
    storage = pool._components
    storage_length = len(storage)

    entity.kill()
    registry.update()

    assert registry.get_component(entity, Position) is None
    assert storage[0] is None

    recycled = registry.create_entity()
    assert recycled.get_id() == entity.get_id()
    assert pool._components is storage
    assert len(storage) == storage_length
    assert registry.get_component(recycled, Position) is None

    replacement = Position(3, 4)
    registry.add_component(recycled, Position, replacement)
    assert storage[0] is replacement
    assert pool._components is storage


def test_stale_entity_cannot_release_a_recycled_slot_twice() -> None:
    registry = Registry()
    stale = registry.create_entity()
    registry.update()
    stale.kill()
    registry.update()

    recycled = registry.create_entity()
    registry.add_component(recycled, Position, Position(10, 20))
    registry.update()

    registry.kill_entity(stale)
    registry.update()

    assert registry.has_component(recycled, Position)
    next_entity = registry.create_entity()
    assert next_entity.get_id() != recycled.get_id()


def test_remove_missing_component_outside_current_pool_is_a_noop() -> None:
    registry = Registry()
    first = registry.create_entity()
    second = registry.create_entity()
    third = registry.create_entity()
    registry.add_component(first, Position, Position())

    registry.remove_component(third, Position)

    assert registry.has_component(first, Position)
    assert not registry.has_component(second, Position)
    assert not registry.has_component(third, Position)


def test_component_lookup_does_not_allocate_unknown_type_id() -> None:
    registry = Registry()
    entity = registry.create_entity()
    unknown = type("UnusedLookupComponent", (Component,), {})
    pool_count = len(registry.component_pools)

    assert registry.get_component(entity, unknown) is None
    assert not registry.has_component(entity, unknown)
    registry.remove_component(entity, unknown)

    assert "_arepy_component_id" not in unknown.__dict__
    assert len(registry.component_pools) == pool_count


def test_direct_component_add_on_active_entity_resyncs_query() -> None:
    from arepy.ecs.entities import Entity
    from arepy.ecs.query import Query, With
    from arepy.ecs.systems import SystemPipeline, SystemState

    registry = Registry()

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        pass

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)
    entity = registry.create_entity()
    registry.add_component(entity, Position, Position())
    registry.update()

    registry.add_component(entity, Velocity, Velocity())
    registry.update()

    query = next(
        argument
        for argument in registry.queries[movement_system]
        if isinstance(argument, Query)
    )
    assert entity in query.get_entities()


def test_system_registered_after_entities_receives_existing_matches() -> None:
    from arepy.ecs.entities import Entity
    from arepy.ecs.query import Query, With
    from arepy.ecs.systems import SystemPipeline, SystemState

    registry = Registry()
    entity = registry.create_entity()
    registry.add_component(entity, Position, Position())
    registry.update()

    def position_system(query: Query[Entity, With[Position]]) -> None:
        pass

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, position_system)

    query = next(
        argument
        for argument in registry.queries[position_system]
        if isinstance(argument, Query)
    )
    assert entity in query.get_entities()


def test_duplicate_system_registration_is_idempotent() -> None:
    from arepy.ecs.entities import Entity
    from arepy.ecs.query import Query, With
    from arepy.ecs.systems import SystemPipeline, SystemState

    registry = Registry()

    def position_system(query: Query[Entity, With[Position]]) -> None:
        pass

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, position_system)
    registered_query = registry.queries[position_system][0]
    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, position_system)

    assert registry.number_of_systems == 1
    assert registry.queries[position_system][0] is registered_query
    assert len(registry._all_queries) == 1


def test_system_execution_preserves_registration_order() -> None:
    from arepy.ecs.systems import SystemPipeline, SystemState

    registry = Registry()
    calls: list[str] = []

    def first() -> None:
        calls.append("first")

    def second() -> None:
        calls.append("second")

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, first)
    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, second)
    registry.run(SystemPipeline.UPDATE)

    assert calls == ["first", "second"]


def test_async_system_does_not_overlap_with_previous_frame() -> None:
    import asyncio

    from arepy.ecs.systems import SystemPipeline, SystemState

    async def scenario() -> None:
        registry = Registry()
        release = asyncio.Event()
        started = asyncio.Event()
        concurrent = 0
        max_concurrent = 0

        async def async_system() -> None:
            nonlocal concurrent, max_concurrent
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
            started.set()
            await release.wait()
            concurrent -= 1

        registry.add_system(SystemPipeline.UPDATE, SystemState.ON, async_system)
        registry.run(SystemPipeline.UPDATE)
        registry.run(SystemPipeline.UPDATE)
        await started.wait()

        assert max_concurrent == 1
        assert len(registry._async_tasks) == 1

        release.set()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    asyncio.run(scenario())


# to run: pytest tests/test_registry.py
