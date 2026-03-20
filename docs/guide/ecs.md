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

In day-to-day gameplay code, `World` is where you:

- create entities
- register systems
- attach world-specific resources
- group scene-specific lifecycle hooks

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

The builder collects components until `build()` is called.

That makes entity setup read like scene construction instead of manual registry plumbing.

## Components

Components are intended to be data holders.

Typical examples include:

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

## World hooks and ECS systems

World hooks are not a replacement for ECS systems. They are best used for small scene-level actions such as:

- initializing world-only state when a scene becomes active
- updating menu or overlay state that is not entity-driven
- running teardown logic when leaving a scene

For gameplay that naturally operates on entities and components, prefer regular systems in `UPDATE`, `RENDER`, or `INPUT` pipelines.

## Registry update model

The registry defers some work until `update()` runs. In practice, this means entity additions, removals, and query synchronization are staged and then applied together. The engine already calls `registry.update()` before running the `UPDATE` pipeline each frame.
