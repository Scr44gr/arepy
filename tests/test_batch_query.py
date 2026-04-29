import pytest

from arepy.ecs import Component
from arepy.ecs.components import ComponentIndex
from arepy.ecs.query import BatchQuery
from arepy.ecs.registry import Registry
from arepy.ecs.systems import SystemPipeline, SystemState
from arepy.math import Vec2


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.value = Vec2(x, y)


class Velocity(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.value = Vec2(x, y)


class Health(Component):
    def __init__(self, value: int = 100):
        super().__init__()
        self.value = value


def test_batch_query_arguments_are_signed() -> None:
    def movement_system(batch: BatchQuery[Position, Velocity]) -> None:
        pass

    from arepy.ecs.query import get_signed_query_arguments

    arguments = get_signed_query_arguments(movement_system)
    batch = arguments["batch"]

    assert isinstance(batch, BatchQuery)
    assert batch.get_component_signature().test(
        ComponentIndex.get_id(Position.__name__)
    )
    assert batch.get_component_signature().test(
        ComponentIndex.get_id(Velocity.__name__)
    )


def test_batch_query_vec2_updates_components_after_system_run() -> None:
    registry = Registry()

    def movement_system(batch: BatchQuery[Position, Velocity]) -> None:
        position = batch.vec2(Position, "value")
        velocity = batch.vec2(Velocity, "value")
        position.x += velocity.x
        position.y += velocity.y

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    entity = registry.create_entity()
    registry.add_component(entity, Position, Position(10.0, 20.0))
    registry.add_component(entity, Velocity, Velocity(1.5, -2.0))
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    position = registry.get_component(entity, Position)
    assert position is not None
    assert position.value.x == pytest.approx(11.5)
    assert position.value.y == pytest.approx(18.0)


def test_batch_query_scalar_updates_components_and_entity_ids_are_sorted() -> None:
    registry = Registry()

    def health_system(batch: BatchQuery[Health]) -> None:
        values = batch.scalar(Health, "value")
        values += batch.entity_ids()

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, health_system)

    entity_one = registry.create_entity()
    entity_two = registry.create_entity()
    registry.add_component(entity_one, Health, Health(10))
    registry.add_component(entity_two, Health, Health(20))
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    health_one = registry.get_component(entity_one, Health)
    health_two = registry.get_component(entity_two, Health)
    assert health_one is not None
    assert health_two is not None
    assert health_one.value == 11
    assert health_two.value == 22


def test_batch_query_rejects_components_outside_annotation() -> None:
    def health_system(batch: BatchQuery[Health]) -> None:
        batch.scalar(Position, "value")

    from arepy.ecs.query import get_signed_query_arguments

    arguments = get_signed_query_arguments(health_system)
    batch = arguments["batch"]

    with pytest.raises(TypeError, match="not part of this BatchQuery"):
        batch.scalar(Position, "value")


def test_batch_query_vec2_stays_in_sync_with_classic_component_mutation() -> None:
    registry = Registry()

    def movement_system(batch: BatchQuery[Position, Velocity]) -> None:
        position = batch.vec2(Position, "value")
        velocity = batch.vec2(Velocity, "value")
        position.x += velocity.x

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    entity = registry.create_entity()
    registry.add_component(entity, Position, Position(5.0, 6.0))
    registry.add_component(entity, Velocity, Velocity(2.0, 0.0))
    registry.update()

    registry.run(SystemPipeline.UPDATE)
    position = registry.get_component(entity, Position)
    assert position is not None
    assert position.value.x == pytest.approx(7.0)

    position.value.x = 42.0
    registry.run(SystemPipeline.UPDATE)

    assert position.value.x == pytest.approx(44.0)
