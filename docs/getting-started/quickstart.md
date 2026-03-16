# Quickstart

Here is a small example you can use to get a feel for the engine.

## Minimal moving entity example

```python
from arepy import ArepyEngine, Renderer2D, SystemPipeline
from arepy.bundle.components import RigidBody2D, Transform
from arepy.ecs import Entities, Query, With
from arepy.math import Vec2


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]],
    renderer: Renderer2D,
) -> None:
    delta_time = renderer.get_delta_time()

    for transform, rigidbody in query.iter_components(Transform, RigidBody2D):
        transform.position.x += rigidbody.velocity.x * delta_time
        transform.position.y += rigidbody.velocity.y * delta_time


engine = ArepyEngine(title="Quickstart")
world = engine.create_world("main")

(
    world.create_entity()
    .with_component(Transform(position=Vec2(32, 32)))
    .with_component(RigidBody2D(velocity=Vec2(60, 20)))
    .build()
)

world.add_system(SystemPipeline.UPDATE, movement_system)
engine.set_current_world("main")
engine.run()
```

## What happens here

- `ArepyEngine` initializes the windowing, rendering, audio, and resource layer
- `create_world()` creates a `World` backed by a fresh ECS `Registry`
- `world.create_entity()` returns an `EntityBuilder`
- `with_component(...)` queues components until `build()` inserts them into the registry
- `world.add_system(...)` registers a callable under a pipeline such as `UPDATE`
- `Query[...]` arguments are inspected when the system is registered, so matching entities are tracked automatically

## Next steps

- Learn the exact frame order in [Engine Lifecycle](../guide/engine-lifecycle.md)
- Learn query filters in [Queries](../guide/queries.md)
- See ready-to-use components in [Built-in Bundle](../guide/bundle.md)
