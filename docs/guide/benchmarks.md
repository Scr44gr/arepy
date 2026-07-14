# Measure ECS performance

Performance changes should be compared with repeatable workloads, not judged
from one FPS counter. The repository includes `benchmarks/ecs_baseline.py` for
that purpose.

## Run a stable comparison

```bash
uv run python benchmarks/ecs_baseline.py \
  --mode all \
  --entities 1000 5000 10000 \
  --runs 10
```

On PowerShell, enter it on one line or use the backtick continuation character.

For useful before/after numbers:

1. Close unrelated heavy applications.
2. Use the same Python build, dependency lock, machine, and power mode.
3. Run the benchmark once to warm caches.
4. Record several runs on the unchanged branch.
5. Apply one architectural change.
6. Repeat the same command and compare medians, not only the best result.

## Modes

| Mode | Focus |
| --- | --- |
| `baseline` | Main entity, query, and lifecycle workflows. |
| `detailed` | Lower-level lookup and query costs. |
| `view` | Direct component-view access. |
| `bundle` | Bundled movement paths and vectorized variants. |
| `all` | Every suite above. |

Start with fewer entities and runs while iterating. Use representative larger
counts before deciding that a change is an improvement.

## Benchmark versus BunnyMark

The harness isolates ECS operations and is appropriate for regressions.
BunnyMark includes rendering, atlas layout, driver work, and presentation, so it
answers a different question: how does the integrated game workload behave?

![BunnyMark showing live entities and FPS](../assets/images/bunnymark.png){ .arepy-screenshot }

Use both when a change affects the ECS-to-render path. Keep the change only
when the targeted benchmark improves without creating a meaningful regression
in the end-to-end frame.

Read [Performance and recycling](performance.md) before interpreting a batch
benchmark.
