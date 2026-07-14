import pytest

from arepy.bundle.components import Transform
from arepy.ecs import Component
from arepy.ecs.components import ComponentIndex
from arepy.ecs.query import BatchQuery
from arepy.ecs.registry import Registry
from arepy.ecs.systems import SystemPipeline, SystemState
from arepy.math import Vec2, Vec3


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


class Position3D(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        super().__init__()
        self.value = Vec3(x, y, z)


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


def test_batch_query_readonly_scalar_uses_requested_dtype_without_writeback() -> None:
    registry = Registry()

    def health_system(batch: BatchQuery[Health]) -> None:
        values = batch.scalar(
            Health,
            "value",
            dtype=float,
            writeback=False,
        )
        values += 5.0
        assert values.dtype.kind == "f"

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, health_system)

    entity = registry.create_entity()
    registry.add_component(entity, Health, Health(10))
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    health = registry.get_component(entity, Health)
    assert health is not None
    assert health.value == 10


def test_batch_query_keeps_vector_storage_for_unrelated_component_changes() -> None:
    registry = Registry()
    storage_ids: list[int] = []

    def movement_system(batch: BatchQuery[Position, Velocity]) -> None:
        position = batch.vec2(Position, "value")
        storage_ids.append(id(position.x))

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    entity = registry.create_entity()
    registry.add_component(entity, Position, Position(1.0, 2.0))
    registry.add_component(entity, Velocity, Velocity(3.0, 4.0))
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    registry.add_component(entity, Health, Health(50), sync_queries=True)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    assert storage_ids[0] == storage_ids[1]


def test_batch_query_bound_scalar_reuses_storage_and_tracks_classic_mutation() -> None:
    registry = Registry()
    storage_ids: list[int] = []
    seen_values: list[float] = []

    def rotation_system(batch: BatchQuery[Transform]) -> None:
        rotation = batch.scalar(Transform, "rotation", dtype=float, bind=True)
        storage_ids.append(id(rotation))
        seen_values.append(float(rotation[0]))
        rotation += 1.0

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, rotation_system)

    entity = registry.create_entity()
    transform = Transform(rotation=10.0)
    registry.add_component(entity, Transform, transform)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    transform.rotation = 25.0
    registry.run(SystemPipeline.UPDATE)

    assert storage_ids[0] == storage_ids[1]
    assert seen_values == [10.0, 25.0]
    assert transform.rotation == pytest.approx(26.0)


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


def test_batch_query_vec2_resyncs_when_another_batch_query_rebinds_storage() -> None:
    registry = Registry()
    seen_positions: list[float] = []

    def movement_system(batch: BatchQuery[Position, Velocity]) -> None:
        position = batch.vec2(Position, "value")
        velocity = batch.vec2(Velocity, "value")
        position.x += velocity.x

    def render_system(batch: BatchQuery[Position, Health]) -> None:
        position = batch.vec2(Position, "value")
        seen_positions.append(float(position.x[0]))

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)
    registry.add_system(SystemPipeline.RENDER, SystemState.ON, render_system)

    entity = registry.create_entity()
    registry.add_component(entity, Position, Position(1.0, 0.0))
    registry.add_component(entity, Velocity, Velocity(2.0, 0.0))
    registry.add_component(entity, Health, Health(1))
    registry.update()

    registry.run(SystemPipeline.UPDATE)
    registry.run(SystemPipeline.RENDER)
    registry.run(SystemPipeline.UPDATE)
    registry.run(SystemPipeline.RENDER)

    assert seen_positions == [pytest.approx(3.0), pytest.approx(5.0)]


def test_batch_query_vec2_preserves_identity_and_validates_every_vector() -> None:
    registry = Registry()
    storage_ids: list[int] = []
    seen_values: list[list[float]] = []

    def capture_system(batch: BatchQuery[Position]) -> None:
        values = batch.vec2(Position, "value")
        storage_ids.append(id(values.x))
        seen_values.append(values.x.tolist())

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_system)
    entity_one = registry.create_entity()
    entity_two = registry.create_entity()
    position_one = Position(1.0, 0.0)
    position_two = Position(2.0, 0.0)
    original_one = position_one.value
    original_two = position_two.value
    replacement = Vec2(100.0, 0.0)
    registry.add_component(entity_one, Position, position_one)
    registry.add_component(entity_two, Position, position_two)
    registry.update()

    registry.run(SystemPipeline.UPDATE)

    assert position_one.value is original_one
    assert position_two.value is original_two

    position_two.value = replacement
    registry.run(SystemPipeline.UPDATE)

    assert position_two.value is replacement
    assert storage_ids[0] == storage_ids[1]
    assert seen_values[-1] == [1.0, 100.0]


def test_batch_query_vec2_detects_non_vector_replacement() -> None:
    registry = Registry()

    def capture_system(batch: BatchQuery[Position]) -> None:
        batch.vec2(Position, "value")

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_system)
    entity = registry.create_entity()
    position = Position(1.0, 2.0)
    registry.add_component(entity, Position, position)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    position.value = object()  # type: ignore[assignment]

    with pytest.raises(TypeError, match="Position.value must be a Vec2"):
        registry.run(SystemPipeline.UPDATE)


def test_batch_query_vec2_detects_deleted_attribute() -> None:
    registry = Registry()

    def capture_system(batch: BatchQuery[Position]) -> None:
        batch.vec2(Position, "value")

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_system)
    entity = registry.create_entity()
    position = Position(7.0, 0.0)
    registry.add_component(entity, Position, position)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    del position.value

    with pytest.raises(AttributeError, match="value"):
        registry.run(SystemPipeline.UPDATE)


def test_batch_query_vector_watcher_handles_child_before_base() -> None:
    class WatchedBasePosition(Component):
        def __init__(self, value: Vec2) -> None:
            self.value = value

    class WatchedChildPosition(WatchedBasePosition):
        pass

    child_registry = Registry()

    def child_system(batch: BatchQuery[WatchedChildPosition]) -> None:
        batch.vec2(WatchedChildPosition, "value")

    child_registry.add_system(SystemPipeline.UPDATE, SystemState.ON, child_system)
    child_entity = child_registry.create_entity()
    child_registry.add_component(
        child_entity,
        WatchedChildPosition,
        WatchedChildPosition(Vec2(1.0, 0.0)),
    )
    child_registry.update()
    child_registry.run(SystemPipeline.UPDATE)

    base_registry = Registry()
    seen: list[list[float]] = []

    def base_system(batch: BatchQuery[WatchedBasePosition]) -> None:
        seen.append(batch.vec2(WatchedBasePosition, "value").x.tolist())

    base_registry.add_system(SystemPipeline.UPDATE, SystemState.ON, base_system)
    base_entity = base_registry.create_entity()
    component = WatchedChildPosition(Vec2(2.0, 0.0))
    replacement = Vec2(9.0, 0.0)
    base_registry.add_component(base_entity, WatchedBasePosition, component)
    base_registry.update()
    base_registry.run(SystemPipeline.UPDATE)

    component.value = replacement
    base_registry.run(SystemPipeline.UPDATE)

    assert seen == [[2.0], [9.0]]


def test_batch_query_vec_buffers_survive_same_size_membership_changes() -> None:
    registry = Registry()
    storage_ids: list[int] = []
    seen_values: list[list[float]] = []

    def capture_system(batch: BatchQuery[Position]) -> None:
        values = batch.vec2(Position, "value")
        storage_ids.append(id(values.x))
        seen_values.append(values.x.tolist())

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_system)
    entity_one = registry.create_entity()
    entity_two = registry.create_entity()
    position_one = Position(1.0, 0.0)
    position_two = Position(2.0, 0.0)
    registry.add_component(entity_one, Position, position_one)
    registry.add_component(entity_two, Position, position_two)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    entity_one.remove_component(Position)
    entity_three = registry.create_entity()
    position_three = Position(3.0, 0.0)
    registry.add_component(entity_three, Position, position_three)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    assert storage_ids[0] == storage_ids[1]
    assert seen_values == [[1.0, 2.0], [2.0, 3.0]]
    assert position_two.value.x == pytest.approx(2.0)
    assert position_three.value.x == pytest.approx(3.0)


def test_batch_query_vec3_preserves_component_vector_identity() -> None:
    registry = Registry()

    def capture_system(batch: BatchQuery[Position3D]) -> None:
        values = batch.vec3(Position3D, "value")
        values.z += 1.0

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, capture_system)
    entity = registry.create_entity()
    position = Position3D(1.0, 2.0, 3.0)
    original = position.value
    registry.add_component(entity, Position3D, position)
    registry.update()
    registry.run(SystemPipeline.UPDATE)

    assert position.value is original
    assert position.value.to_tuple() == pytest.approx((1.0, 2.0, 4.0))


def test_batch_query_non_bound_scalar_reuses_buffer_after_exception() -> None:
    registry = Registry()
    buffers: list[object] = []
    should_fail = True

    def health_system(batch: BatchQuery[Health]) -> None:
        values = batch.scalar(Health, "value", dtype=float)
        buffers.append(values)
        values += 5.0
        if should_fail:
            raise RuntimeError("stop before writeback")

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, health_system)
    entity = registry.create_entity()
    health = Health(10)
    registry.add_component(entity, Health, health)
    registry.update()

    with pytest.raises(RuntimeError, match="stop before writeback"):
        registry.run(SystemPipeline.UPDATE)
    assert health.value == pytest.approx(15.0)

    should_fail = False
    registry.run(SystemPipeline.UPDATE)
    assert health.value == pytest.approx(20.0)

    registry.run(SystemPipeline.UPDATE)
    assert health.value == pytest.approx(25.0)
    assert buffers[0] is buffers[1] is buffers[2]


def test_batch_query_bound_scalar_detects_partial_rebinds() -> None:
    registry = Registry()
    storages: list[object] = []
    seen_values: list[list[float]] = []

    def rotation_system(batch: BatchQuery[Transform]) -> None:
        values = batch.scalar(Transform, "rotation", dtype=float, bind=True)
        storages.append(values)
        seen_values.append(values.tolist())

    def subset_system(batch: BatchQuery[Transform, Health]) -> None:
        values = batch.scalar(Transform, "rotation", dtype=float, bind=True)
        values[0] = 99.0

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, rotation_system)
    registry.add_system(SystemPipeline.RENDER, SystemState.ON, subset_system)
    entity_one = registry.create_entity()
    entity_two = registry.create_entity()
    transform_one = Transform(rotation=10.0)
    transform_two = Transform(rotation=20.0)
    registry.add_component(entity_one, Transform, transform_one)
    registry.add_component(entity_two, Transform, transform_two)
    registry.add_component(entity_two, Health, Health(1))
    registry.update()
    registry.run(SystemPipeline.UPDATE)
    registry.run(SystemPipeline.RENDER)
    registry.run(SystemPipeline.UPDATE)

    assert storages[0] is storages[1]
    assert seen_values == [[10.0, 20.0], [10.0, 99.0]]


def test_batch_query_vec2_rejects_non_vector_attributes() -> None:
    registry = Registry()

    def invalid_system(batch: BatchQuery[Position]) -> None:
        batch.vec2(Position, "value")

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, invalid_system)
    entity = registry.create_entity()
    position = Position()
    position.value = 42  # type: ignore[assignment]
    registry.add_component(entity, Position, position)
    registry.update()

    with pytest.raises(TypeError, match=r"Position\.value must be a Vec2"):
        registry.run(SystemPipeline.UPDATE)
