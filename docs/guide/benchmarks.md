# Benchmarks

The repository includes a persistent ECS benchmark harness in `benchmarks/ecs_baseline.py`.

## Run the benchmark suite

```bash
uv run python benchmarks/ecs_baseline.py
uv run python benchmarks/ecs_baseline.py --entities 1000 5000 10000 --runs 10
uv run python benchmarks/ecs_baseline.py --mode detailed --entities 1000 5000 10000 --runs 10
uv run python benchmarks/ecs_baseline.py --mode view --entities 1000 5000 10000 --runs 10
uv run python benchmarks/ecs_baseline.py --mode bundle --entities 1000 5000 10000 --runs 10
```

## Current modes

- `baseline` measures the main ECS workflow costs
- `detailed` isolates lower-level query and lookup costs
- `view` focuses on direct component-view style access
- `bundle` compares bundled movement scenarios
- `all` runs every mode

## When to use it

Use the benchmark harness when you change:

- registry synchronization behavior
- query iteration paths
- component pool access
- bundled systems that run every frame

## Practical advice

Start with a small entity count while iterating locally, then rerun with the larger sizes before you compare branches or prepare a performance report.
