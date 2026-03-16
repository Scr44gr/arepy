# ECS Basics

Arepy's ECS layer lives under `arepy.ecs` and revolves around a few small concepts.

## `World`

`World` is the public façade you normally use in gameplay code.

The most common calls look like this:

```python
world = engine.create_world(name: str)
builder = world.create_entity()
world.add_system(pipeline: SystemPipeline, system: Callable[..., object])
```

Its tested responsibilities are:

- create entities through `create_entity()`
- add one or many systems to a pipeline
- change the state of a system
- expose the underlying registry when you need lower-level access

## Entities and `EntityBuilder`

`world.create_entity()` returns an `EntityBuilder`.

You then pass component instances into `with_component(component: Component)` and finish with `build() -> Entity`.

```python
player = (
    world.create_entity()
    .with_component(Transform(position=Vec2(100, 100)))
    .with_component(RigidBody2D(velocity=Vec2(50, 0)))
    .build()
)
```

The builder collects components until `build()` is called. Tests currently verify that:

- only `Component` instances can be added
- the same component type cannot be added twice to one builder
- `build()` inserts every queued component into the registry

## Components

Components are intended to be data holders.

That guidance is visible both in the project structure and in the existing tests. Typical examples include:

- `Transform`
- `RigidBody2D`
- `Sprite`
- custom gameplay data like `Health`, `Position`, or `Velocity`

## Systems

Systems are plain callables registered in a `SystemPipeline`.

```python
world.add_system(SystemPipeline.UPDATE, movement_system)
```

The first argument is the pipeline enum value. The second argument is the function to run.

```python
def movement_system(
    query: Query[Entity, With[Transform, RigidBody2D]],
    renderer: Renderer2D,
) -> None:
    ...
```

The registry inspects function annotations at registration time. Query parameters become signed `Query` objects, and class-typed parameters can be resolved from the resource container.

## Registry update model

The registry defers some work until `update()` runs. In practice, this means entity additions, removals, and query synchronization are staged and then applied together. The engine already calls `registry.update()` before running the `UPDATE` pipeline each frame.
