# Queries: ask the world for the right data

A system should not scan every entity and ask what it contains. A query states
the requirement once, and Arepy keeps the matching set synchronized as the world
changes.

The most useful habit is to read a query like an English sentence:

```python
Query[Entity, With[Transform, RigidBody2D]]
```

> Give me every entity **with** both `Transform` and `RigidBody2D`.

Queries are declared as system annotations. Arepy creates and supplies them when
the system is registered; application code does not instantiate them.

## Describe what must be present—or absent

Import the query building blocks from `arepy.ecs`:

```python
from arepy import Time
from arepy.bundle.components.rigidbody import RigidBody2D
from arepy.bundle.components.transform import Transform
from arepy.ecs import Entity, Query, With, Without
```

`With[...]` requires every listed component:

```python
Query[Entity, With[Transform, Health]]
```

`Without[...]` excludes entities that have any listed component:

```python
Query[Entity, Without[Disabled]]
```

Combine the two in a tuple:

```python
Query[
    Entity,
    tuple[With[Transform, RigidBody2D], Without[Frozen]],
]
```

That last query says: “entities with a transform and rigid body, unless they
are frozen.” The filter affects membership; it is not an `if` check repeated for
every entity on every iteration.

## Choose what the loop needs

All three iteration styles use the same matching query. Choose based on the data
needed inside the loop.

### Components only

Use `iter_components(...)` for the common case where the behavior only reads or
changes component data:

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

The returned tuple follows the same order as the component types passed to the
method. With one component, unpack the one-item tuple:

```python
for (health,) in query.iter_components(Health):
    health.current = min(health.maximum, health.current + 1)
```

This is the preferred object-oriented hot path because it avoids looking up the
same components through each entity handle.

### Entity plus components

Use `iter_entities_components(...)` when the behavior also needs identity—for
example, to kill an entity or put its handle in an event:

```python
for entity, transform, health in query.iter_entities_components(
    Transform,
    Health,
):
    if health.current <= 0:
        entity.kill()
```

The entity is first, followed by components in the requested order.

### Entity only

Iterate the query directly when identity is all that matters:

```python
for entity in query:
    selected_ids.append(entity.get_id())
```

Normal query iteration is ordered by entity ID, which makes a frame easier to
reason about. `get_entities()` exposes the underlying set; do not use that set
when order matters.

!!! tip "Ask only for components guaranteed by the filter"

    The types passed to `iter_components(...)` or
    `iter_entities_components(...)` should be included by the query's
    `With[...]` filter. This keeps the system's promise clear to both readers and
    the engine.

## Query membership follows structural synchronization

If an entity gains or loses a component, or is created or killed, its membership
is refreshed at the next ECS synchronization point. The engine performs this
before `UPDATE`.

Iteration remains stable during the current system run. Calling `kill()` inside
a query loop is therefore safe, but the current loop is not restarted and the
entity does not disappear halfway through it. See [ECS basics](ecs.md#structural-changes-are-synchronized-safely)
for the full lifecycle.

## Query or BatchQuery?

`Query` and `BatchQuery` solve different shapes of work:

| Use `Query` when… | Use `BatchQuery` when… |
| --- | --- |
| each entity follows different branches | many entities receive the same numeric operation |
| you call object-oriented APIs | NumPy can express the work as array operations |
| you need `Without[...]` filters | requiring all listed component types is enough |
| the matching group is small | the matching group is large enough to repay vectorization overhead |

There is no universal entity-count threshold. A straightforward `Query` can be
faster for a small or branch-heavy group, while `BatchQuery` shines for large,
regular updates. Measure the real scene instead of choosing by reputation.

## BatchQuery: update columns together

A batch query lists the component types required by the operation:

```python
import numpy as np

from arepy import Time
from arepy.ecs import BatchQuery


def movement_system(
    batch: BatchQuery[Transform, RigidBody2D],
    time: Time,
) -> None:
    position = batch.vec2(Transform, "position")
    velocity = batch.vec2(RigidBody2D, "velocity")

    position.x += velocity.x * time.delta_seconds
    position.y += velocity.y * time.delta_seconds
```

Every row represents one matching entity, and the arrays from different batch
accessors use the same entity order.

`BatchQuery` currently expresses required component types only: the example
matches entities that have both `Transform` and `RigidBody2D`. Use a normal
`Query` when an exclusion such as `Without[Frozen]` is essential, or model an
included group with an explicit marker component.

### Vec2 and Vec3 fields

Use `vec2(...)` for a component field containing Arepy `Vec2` values and
`vec3(...)` for `Vec3` values:

```python
position_2d = batch.vec2(Transform, "position")
position_2d.x += 4.0
position_2d.y *= 0.98

position_3d = batch.vec3(Transform3D, "position")
position_3d.z -= 2.0
```

Their `x`, `y`, and `z` members are NumPy arrays bound to the vectors. In-place
changes update component values directly; there is no per-row writeback loop in
your system. With stable query membership, Arepy reuses those arrays across
frames.

Replacing an entire component vector is supported, but requires the batch to
notice and bind the replacement. In hot paths, prefer mutating existing values:

```python
# Preferred in a per-frame system
transform.position.x = spawn_x
transform.position.y = spawn_y

# Creates a new vector and may require a batch rebind
transform.position = Vec2(spawn_x, spawn_y)
```

### Scalar fields

`scalar(...)` supports three useful data-flow modes:

| Call | Behavior | Best for |
| --- | --- | --- |
| `scalar(Type, "field")` | refreshes a NumPy buffer, then writes changes back after the system returns | ordinary mutable numeric fields |
| `scalar(Type, "field", writeback=False)` | refreshes a snapshot but does not copy edits back to components | read-only calculations |
| `scalar(Type, "field", bind=True)` | uses specialized persistent backing storage; edits are immediately visible | fields whose component type explicitly supports binding |

The default mode works with a normal Python field:

```python
def poison_system(batch: BatchQuery[Health], time: Time) -> None:
    health = batch.scalar(Health, "current", dtype=np.float64)
    health -= 8.0 * time.delta_seconds
    np.maximum(health, 0.0, out=health)
    # Arepy writes the values to Health.current when this system returns.
```

For a read-only snapshot, changes to the returned array are local and are not
written back:

```python
limits = batch.scalar(
    RigidBody2D,
    "max_velocity",
    dtype=np.float64,
    writeback=False,
)
```

Binding is intentionally specialized; it is not available for every arbitrary
field. `Transform.rotation` supports it:

```python
def spin_system(batch: BatchQuery[Transform], time: Time) -> None:
    rotation = batch.scalar(
        Transform,
        "rotation",
        dtype=np.float64,
        bind=True,
    )
    rotation += 90.0 * time.delta_seconds
```

If a component field does not support bound scalar storage, `bind=True` raises
`TypeError`. Use default writeback for that field instead.

### IDs and component objects

Batch queries can also expose aligned IDs and component objects:

```python
ids = batch.entity_ids()                 # NumPy array of entity IDs
sprites = batch.components(Sprite)       # list of Sprite objects
```

`entity_ids()` is useful for deterministic numeric rules. `components()` is
useful when another API needs component objects, such as preparing a sprite
layout, but looping over that list is still an object loop rather than a
vectorized operation.

## Work with reusable buffers safely

Arepy caches query rows and batch buffers while membership and component layout
remain stable. Follow these rules so that optimization stays correct:

1. Request the batch view inside each system invocation. It is cheap in the
   steady state and refreshes correctly after structural changes.
2. Do not resize, reorder, or replace the NumPy arrays returned by a batch.
3. Use in-place operations (`+=`, `*=`, `np.maximum(..., out=...)`) when they
   express the behavior clearly.
4. Reacquire views after spawning, killing, or changing the relevant component
   set; do not treat an old array reference as permanent world storage.
5. Keep arrays from the same batch invocation together so their rows remain
   aligned.

For rendering and other large workloads, combine batch queries with texture
atlases and batched draw calls. The next step is [Performance](performance.md).
