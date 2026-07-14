# Performance: protect the frame budget

Performance work is not about making every line clever. It is about finding the
code that runs many times per frame, removing repeated work from that path, and
measuring the result.

At 60 FPS a complete frame has about **16.67 ms**. At 120 FPS it has about
**8.33 ms**. Input, gameplay, rendering, UI, and the operating system all share
that budget, so a small cost repeated across thousands of entities matters.

## First, identify the hot path

A hot path is code whose cost is multiplied by frequency:

- a system that runs every frame;
- a loop over thousands of entities;
- a renderer call issued once per sprite;
- an allocation repeated for every object or every frame.

Setup, scene loading, and a button clicked once do not need the same treatment.
Keep those paths readable unless a profile shows that they are a real problem.

## Avoid repeated component lookup and reflection

The readable and efficient object path is `iter_components(...)`:

```python
def movement_system(
    query: Query[Entity, With[Transform, RigidBody2D]],
    time: Time,
) -> None:
    dt = time.delta_seconds

    for transform, body in query.iter_components(Transform, RigidBody2D):
        transform.position.x += body.velocity.x * dt
        transform.position.y += body.velocity.y * dt
```

Avoid discovering known fields dynamically inside an entity loop:

```python
# Avoid this shape in a per-frame loop.
for entity in query:
    transform = entity.get_component(Transform)
    position = getattr(transform, "position")
    setattr(position, "x", position.x + 1.0)
```

`entity.get_component(...)`, `getattr(...)`, and `setattr(...)` all add repeated
Python work here. When the component types and field names are already known,
iterate the components and access their fields directly.

## Mutate existing values instead of replacing them

Arepy vectors are mutable. Update them in place:

```python
# Reuses the existing Vec2.
transform.position.x += body.velocity.x * dt
transform.position.y += body.velocity.y * dt
```

Creating a fresh vector every frame creates garbage and can force a `BatchQuery`
to rebind its storage:

```python
# Avoid in a hot loop when an in-place update is enough.
transform.position = Vec2(
    transform.position.x + body.velocity.x * dt,
    transform.position.y + body.velocity.y * dt,
)
```

Apply the same principle to lists, NumPy scratch arrays, colors, rectangles, and
other temporary data. Keep reusable state in a world resource when it needs a
lifetime longer than one function call.

## Load assets once

Disk access, image decoding, texture upload, font creation, and audio decoding do
not belong in a per-frame system. Load assets during setup and keep their IDs or
handles:

```python
asset_store = game.get_asset_store()
renderer = game.renderer_2d

asset_store.load_texture(
    renderer,
    "bunny.png",
    "assets/bunny.png",
)
asset_store.build_texture_atlas(renderer)
```

Systems should draw an already loaded asset. The same rule applies to sounds:
load them once, then play the existing sound object when an event occurs.

## Reuse ECS storage deliberately

Calling `entity.kill()` does not make the registry grow forever. At structural
synchronization Arepy clears the component slots, increments the entity
generation, and makes the numeric slot available to a future spawn. Component
pool capacity remains available for reuse.

That is valuable for projectiles, enemies, particles, and other short-lived
entities, but it does not make spawning free. A respawn still creates a new
entity handle and the Python component values supplied to the builder.

Choose the lifecycle that matches the game:

- If the object truly ends, call `kill()` and let the ECS recycle its slots.
- If the exact object is merely inactive and will return soon, consider keeping
  it alive, toggling an active marker/state, and resetting its existing fields.
- Do not kill and recreate every entity each frame just to change its position,
  visibility, or animation state.

Read [What pooling and generations actually reuse](ecs.md#what-pooling-and-generations-actually-reuse)
for the exact lifecycle.

## Use BatchQuery for regular numeric work

When thousands of entities receive the same arithmetic, move the loop into
NumPy with `BatchQuery`:

```python
import numpy as np


def movement_system(
    batch: BatchQuery[Transform, RigidBody2D],
    time: Time,
) -> None:
    position = batch.vec2(Transform, "position")
    velocity = batch.vec2(RigidBody2D, "velocity")

    position.x += velocity.x * time.delta_seconds
    position.y += velocity.y * time.delta_seconds

    left = position.x < 0.0
    position.x[left] = 0.0
    velocity.x[left] = np.abs(velocity.x[left])
```

The ECS reuses vector and scalar buffers when membership is stable. Request the
views each run and mutate them in place. For extremely hot NumPy code, profiles
may reveal temporary arrays such as masks as the next cost; reuse scratch arrays
or `out=` operations only after measuring that they help.

`BatchQuery` is not a blanket replacement for `Query`. Branch-heavy behavior,
small groups, and object API calls can be clearer and faster with normal
component iteration. See [Query or BatchQuery?](queries.md#query-or-batchquery).

## Batch rendering, not just simulation

Optimizing movement while issuing one expensive draw setup per sprite moves the
bottleneck rather than removing it. For large groups of sprites:

1. load textures before the game loop;
2. build a texture atlas once;
3. cache stable sprite layout data;
4. pass aligned position, origin, rotation, and layout arrays to
   `renderer.draw_texture_batch(...)`.

The BunnyMark example uses this arrangement: `BatchQuery` updates positions,
the atlas groups the bunny texture, and one batch-oriented rendering path draws
the large group. Rebuild atlas or layout data only when the underlying assets or
sprite layout actually change.

## Keep per-frame allocations visible

Common accidental allocations include:

- constructing `Vec2`, `Vec3`, `Color`, or configuration objects in every loop;
- creating a list only to iterate it once;
- converting the same component data to a NumPy array every frame;
- rebuilding a texture atlas or batch layout without a layout change;
- formatting large debug strings when the overlay is hidden;
- registering systems, callbacks, or resources from an update system.

Not every temporary is harmful. Remove the ones that appear in a measured hot
path, and keep code straightforward elsewhere.

## Measure every architectural change

Run a benchmark before and after a change under the same conditions:

```bash
uv run python benchmarks/ecs_baseline.py --mode all --entities 1000 5000 10000 --runs 10
```

Use a focused mode while iterating:

| Mode | What it helps compare |
| --- | --- |
| `baseline` | creation, component changes, query sync, recycling |
| `view` | entity lookup versus component-row iteration |
| `bundle` | normal movement, `BatchQuery`, scalar binding, steady buffers |
| `detailed` | lower-level lookup and system overhead |

For trustworthy comparisons:

1. use the same machine, Python version, power mode, entity counts, and run
   count;
2. close debuggers and unrelated heavy applications;
3. compare medians and variability, not one unusually fast sample;
4. repeat the benchmark if the result is close to normal run-to-run noise;
5. run a representative game scene and inspect frame time and FPS as the final
   validation.

A microbenchmark can show *where* a change helps, but the player experiences the
whole frame. Keep an architectural change only when it improves the relevant
workload without causing a meaningful regression elsewhere. See the
[benchmark guide](benchmarks.md) for the available suites.

## Practical checklist

Before calling a performance-sensitive feature ready, check that:

- assets and stable layouts are created outside the frame loop;
- systems use `iter_components(...)` or an appropriate `BatchQuery`;
- known fields use direct access rather than reflection in hot loops;
- vectors and arrays are mutated in place;
- spawn/despawn represents a real lifecycle change;
- large render groups use an atlas and batch draw path;
- before/after benchmark results were recorded under comparable conditions;
- the real scene holds its target frame rate.
