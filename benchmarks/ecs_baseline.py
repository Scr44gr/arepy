from __future__ import annotations

import argparse
import gc
import statistics
from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Iterable, cast

from arepy.ecs.components import Component, ComponentIndex, ComponentPool
from arepy.ecs.entities import Entity
from arepy.ecs.query import Query, With
from arepy.ecs.registry import Registry
from arepy.ecs.systems import SystemPipeline, SystemState

BenchmarkAction = Callable[[], None]
BenchmarkFactory = Callable[[int], BenchmarkAction]
BLACKHOLE = 0


class Position(Component):
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


class Velocity(Component):
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


class Health(Component):
    __slots__ = ("value",)

    def __init__(self, value: int = 100):
        super().__init__()
        self.value = value


@dataclass(slots=True)
class BenchmarkResult:
    name: str
    entity_count: int
    runs: int
    mean_seconds: float
    stdev_seconds: float
    min_seconds: float
    max_seconds: float

    @property
    def mean_ms(self) -> float:
        return self.mean_seconds * 1000.0

    @property
    def throughput(self) -> float:
        if self.mean_seconds == 0:
            return 0.0
        return self.entity_count / self.mean_seconds


def create_registry_with_entities(entity_count: int) -> tuple[Registry, list[Entity]]:
    registry = Registry()
    entities = [registry.create_entity() for _ in range(entity_count)]
    return registry, entities


def consume(value: int) -> None:
    global BLACKHOLE
    BLACKHOLE ^= value


def get_registered_query(registry: Registry, system: Callable[..., None]) -> Query:
    for argument in registry.queries[system]:
        if isinstance(argument, Query):
            return argument
    raise ValueError(f"System {system.__name__} does not have a registered query.")


def create_populated_registry(entity_count: int) -> tuple[Registry, list[Entity]]:
    registry, entities = create_registry_with_entities(entity_count)
    for index, entity in enumerate(entities):
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, -1.0))
        registry.add_component(entity, Health, Health(100))
    registry.update()
    return registry, entities


def create_registry_with_position_velocity_query(
    entity_count: int,
) -> tuple[Registry, list[Entity], Query]:
    registry = Registry()

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        return None

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    entities = [registry.create_entity() for _ in range(entity_count)]
    for index, entity in enumerate(entities):
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, 1.0))

    registry.update()
    query = get_registered_query(registry, movement_system)
    return registry, entities, query


def get_component_pool(
    registry: Registry, component_type: type[Component]
) -> ComponentPool:
    component_id = ComponentIndex.get_id(component_type.__name__)
    pool = registry.component_pools[component_id - 1]
    if pool is None:
        raise ValueError(
            f"Component pool for {component_type.__name__} is not initialized."
        )
    return cast(ComponentPool, pool)


def make_benchmark_create_entities(entity_count: int) -> BenchmarkAction:
    def action() -> None:
        registry = Registry()
        for _ in range(entity_count):
            registry.create_entity()

    return action


def make_benchmark_add_components(entity_count: int) -> BenchmarkAction:
    registry, entities = create_registry_with_entities(entity_count)

    def action() -> None:
        for index, entity in enumerate(entities):
            registry.add_component(
                entity, Position, Position(float(index), float(index))
            )
            registry.add_component(entity, Velocity, Velocity(1.0, -1.0))
            registry.add_component(entity, Health, Health(100))

    return action


def make_benchmark_update_query_sync(entity_count: int) -> BenchmarkAction:
    registry = Registry()

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        return None

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    for index in range(entity_count):
        entity = registry.create_entity()
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(0.5, 0.25))

    def action() -> None:
        registry.update()

    return action


def make_benchmark_run_movement_system(entity_count: int) -> BenchmarkAction:
    registry = Registry()

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        total = 0
        for entity in query.get_entities():
            position = entity.get_component(Position)
            velocity = entity.get_component(Velocity)
            position.x += velocity.x
            position.y += velocity.y
            total += int(position.x + position.y + velocity.x + velocity.y)
        consume(total)

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    for index in range(entity_count):
        entity = registry.create_entity()
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, 1.0))

    registry.update()

    def action() -> None:
        registry.run(SystemPipeline.UPDATE)

    return action


def make_benchmark_remove_components(entity_count: int) -> BenchmarkAction:
    registry, entities = create_registry_with_entities(entity_count)
    for index, entity in enumerate(entities):
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, -1.0))

    registry.update()

    def action() -> None:
        for entity in entities:
            registry.remove_component(entity, Velocity)

        registry.update()

    return action


def make_benchmark_query_iterate_only(entity_count: int) -> BenchmarkAction:
    registry = Registry()

    def query_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        return None

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, query_system)

    for index in range(entity_count):
        entity = registry.create_entity()
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, 1.0))

    registry.update()
    query = get_registered_query(registry, query_system)

    def action() -> None:
        total = 0
        for entity in query.get_entities():
            total += entity.get_id()
        consume(total)

    return action


def make_benchmark_entity_cache_hits(entity_count: int) -> BenchmarkAction:
    _, entities = create_populated_registry(entity_count)

    for entity in entities:
        entity.get_component(Position)
        entity.get_component(Velocity)

    def action() -> None:
        total = 0
        for entity in entities:
            position = entity.get_component(Position)
            velocity = entity.get_component(Velocity)
            total += int(position.x + position.y + velocity.x + velocity.y)
        consume(total)

    return action


def make_benchmark_registry_get_component(entity_count: int) -> BenchmarkAction:
    registry, entities = create_populated_registry(entity_count)

    def action() -> None:
        total = 0
        for entity in entities:
            position = registry.get_component(entity, Position)
            velocity = registry.get_component(entity, Velocity)
            total += int(position.x + position.y + velocity.x + velocity.y)  # type: ignore[union-attr]
        consume(total)

    return action


def make_benchmark_system_iter_only(entity_count: int) -> BenchmarkAction:
    registry = Registry()

    def iter_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        total = 0
        for entity in query.get_entities():
            total += entity.get_id()
        consume(total)

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, iter_system)

    for index in range(entity_count):
        entity = registry.create_entity()
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, 1.0))

    registry.update()

    def action() -> None:
        registry.run(SystemPipeline.UPDATE)

    return action


def make_benchmark_pool_lookup_by_entity_id(entity_count: int) -> BenchmarkAction:
    registry, _, query = create_registry_with_position_velocity_query(entity_count)
    position_pool = get_component_pool(registry, Position)
    velocity_pool = get_component_pool(registry, Velocity)

    def action() -> None:
        total = 0
        for entity in query.get_entities():
            index = entity.get_id() - 1
            position = cast(Position, position_pool[index])
            velocity = cast(Velocity, velocity_pool[index])
            position.x += velocity.x
            position.y += velocity.y
            total += int(position.x + position.y + velocity.x + velocity.y)
        consume(total)

    return action


def make_benchmark_query_iter_components(entity_count: int) -> BenchmarkAction:
    _, _, query = create_registry_with_position_velocity_query(entity_count)

    def action() -> None:
        total = 0
        for position, velocity in query.iter_components(Position, Velocity):
            typed_position = cast(Position, position)
            typed_velocity = cast(Velocity, velocity)
            typed_position.x += typed_velocity.x
            typed_position.y += typed_velocity.y
            total += int(
                typed_position.x
                + typed_position.y
                + typed_velocity.x
                + typed_velocity.y
            )
        consume(total)

    return action


def make_benchmark_system_move_with_view(entity_count: int) -> BenchmarkAction:
    registry = Registry()

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        total = 0
        for position, velocity in query.iter_components(Position, Velocity):
            typed_position = cast(Position, position)
            typed_velocity = cast(Velocity, velocity)
            typed_position.x += typed_velocity.x
            typed_position.y += typed_velocity.y
            total += int(
                typed_position.x
                + typed_position.y
                + typed_velocity.x
                + typed_velocity.y
            )
        consume(total)

    registry.add_system(SystemPipeline.UPDATE, SystemState.ON, movement_system)

    for index in range(entity_count):
        entity = registry.create_entity()
        registry.add_component(entity, Position, Position(float(index), float(index)))
        registry.add_component(entity, Velocity, Velocity(1.0, 1.0))

    registry.update()

    def action() -> None:
        registry.run(SystemPipeline.UPDATE)

    return action


def make_benchmark_dense_pool_scan(entity_count: int) -> BenchmarkAction:
    registry, _ = create_populated_registry(entity_count)
    position_pool = get_component_pool(registry, Position)
    velocity_pool = get_component_pool(registry, Velocity)

    def action() -> None:
        total = 0
        for position, velocity in zip(position_pool.get_all(), velocity_pool.get_all()):
            if position is None or velocity is None:
                continue
            position.x += velocity.x
            position.y += velocity.y
            total += int(position.x + position.y + velocity.x + velocity.y)
        consume(total)

    return action


def make_benchmark_prebuilt_component_pairs(entity_count: int) -> BenchmarkAction:
    registry, _ = create_populated_registry(entity_count)
    position_pool = get_component_pool(registry, Position)
    velocity_pool = get_component_pool(registry, Velocity)
    component_pairs = [
        (cast(Position, position), cast(Velocity, velocity))
        for position, velocity in zip(position_pool.get_all(), velocity_pool.get_all())
        if position is not None and velocity is not None
    ]

    def action() -> None:
        total = 0
        for position, velocity in component_pairs:
            position.x += velocity.x
            position.y += velocity.y
            total += int(position.x + position.y + velocity.x + velocity.y)
        consume(total)

    return action


def run_benchmark(
    name: str,
    entity_count: int,
    runs: int,
    benchmark_factory: BenchmarkFactory,
) -> BenchmarkResult:
    samples: list[float] = []
    for _ in range(runs):
        gc.collect()
        benchmark_fn = benchmark_factory(entity_count)
        started = perf_counter()
        benchmark_fn()
        ended = perf_counter()
        samples.append(ended - started)

    mean_seconds = statistics.mean(samples)
    stdev_seconds = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return BenchmarkResult(
        name=name,
        entity_count=entity_count,
        runs=runs,
        mean_seconds=mean_seconds,
        stdev_seconds=stdev_seconds,
        min_seconds=min(samples),
        max_seconds=max(samples),
    )


def format_results(results: Iterable[BenchmarkResult]) -> str:
    lines = [
        "scenario                        entities  mean_ms   stdev_ms  min_ms    max_ms    entities/s",
        "------------------------------  --------  --------  --------  --------  --------  ----------",
    ]
    for result in results:
        lines.append(
            f"{result.name:<30}  "
            f"{result.entity_count:>8}  "
            f"{result.mean_ms:>8.3f}  "
            f"{result.stdev_seconds * 1000.0:>8.3f}  "
            f"{result.min_seconds * 1000.0:>8.3f}  "
            f"{result.max_seconds * 1000.0:>8.3f}  "
            f"{result.throughput:>10.0f}"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Baseline ECS benchmark for Arepy.")
    parser.add_argument(
        "--entities",
        type=int,
        nargs="+",
        default=[1_000, 5_000, 10_000],
        help="Entity counts to benchmark.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of times to repeat each scenario.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "detailed", "view", "all"],
        default="all",
        help="Which benchmark suite to run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline_scenarios: list[tuple[str, BenchmarkFactory]] = [
        ("create_entities", make_benchmark_create_entities),
        ("add_components_3x", make_benchmark_add_components),
        ("update_query_sync", make_benchmark_update_query_sync),
        ("run_movement_system", make_benchmark_run_movement_system),
        ("remove_component_sync", make_benchmark_remove_components),
    ]
    detailed_scenarios: list[tuple[str, BenchmarkFactory]] = [
        ("query_iterate_only", make_benchmark_query_iterate_only),
        ("entity_cache_hits_2x", make_benchmark_entity_cache_hits),
        ("registry_get_component_2x", make_benchmark_registry_get_component),
        ("system_iter_only", make_benchmark_system_iter_only),
        ("system_move_with_lookup", make_benchmark_run_movement_system),
    ]
    view_scenarios: list[tuple[str, BenchmarkFactory]] = [
        ("system_move_with_lookup", make_benchmark_run_movement_system),
        ("query_iter_components", make_benchmark_query_iter_components),
        ("system_move_with_view", make_benchmark_system_move_with_view),
        ("pool_lookup_by_entity_id", make_benchmark_pool_lookup_by_entity_id),
        ("dense_pool_scan", make_benchmark_dense_pool_scan),
        ("prebuilt_component_pairs", make_benchmark_prebuilt_component_pairs),
    ]

    scenarios: list[tuple[str, BenchmarkFactory]] = []
    if args.mode in ("baseline", "all"):
        scenarios.extend(baseline_scenarios)
    if args.mode in ("detailed", "all"):
        scenarios.extend(detailed_scenarios)
    if args.mode in ("view", "all"):
        scenarios.extend(view_scenarios)

    results: list[BenchmarkResult] = []
    for entity_count in args.entities:
        for name, benchmark_factory in scenarios:
            results.append(
                run_benchmark(name, entity_count, args.runs, benchmark_factory)
            )

    print(format_results(results))


if __name__ == "__main__":
    main()
