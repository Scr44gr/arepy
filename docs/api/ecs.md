# ECS API

This page highlights the ECS types you will touch most often.

- `World` is where entities, resources, and systems live.
- `EntityBuilder` gives you a friendly way to create entities.
- `Component` is the base type for ECS components.
- `Entity` is the lightweight identifier used by the world.
- `Query`, `With`, and `Without` help filter entities.

## Start here if you want to...

- create entities and attach components
- register gameplay systems into `UPDATE`, `RENDER`, or `INPUT`
- add world-local resources for one scene
- understand where `Query`, `With`, and `Without` fit into normal gameplay code

## Main concepts

### `World`

`World` is the place where scene-level ECS work happens.

Typical usage looks like this:

```python
world = engine.create_world("main")

player = (
	world.create_entity()
	.with_component(Transform(...))
	.with_component(Sprite(...))
	.build()
)

world.add_system(SystemPipeline.UPDATE, movement_system)
world.add_system(SystemPipeline.RENDER, render_system)
```

Worlds now support two related ideas:

- local resources that only belong to that world
- lifecycle hooks such as `world.on_startup` and `world.on_shutdown`

That makes `World` more than just a thin wrapper around the registry. It becomes the public scene object you shape during normal game setup.

### `EntityBuilder`

`EntityBuilder` is the fluent way to create entities without manually touching component pools or signatures.

It is a good fit when scene creation is mostly declarative: “spawn this entity with these components”.

### `Query`, `With`, and `Without`

Queries are the main filtering tool for gameplay systems.

```python
def movement_system(
	query: Query[Entity, With[Transform, Velocity]],
	renderer: Renderer2D,
) -> None:
	...
```

That signature reads as: “run this system over entities that have `Transform` and `Velocity`, and also give me access to the renderer service”.

### Resource lookup inside ECS systems

When a system parameter is a class type such as `Renderer2D` or `GameSettings`, Arepy resolves it from resources.

The lookup order is:

1. current world resources
2. global engine resources

That lets you keep scene state local while still using the shared engine services everywhere.

## Good companion pages

- [ECS Basics](../guide/ecs.md)
- [Queries](../guide/queries.md)
- [Resources and Systems](../guide/resources.md)

## Generated reference

- [World module](reference/arepy/ecs/world/)
- [Registry module](reference/arepy/ecs/registry/)
- [Builders module](reference/arepy/ecs/builders/)
- [Components module](reference/arepy/ecs/components/)
- [Entities module](reference/arepy/ecs/entities/)
- [Query module](reference/arepy/ecs/query/)

## Where to keep reading

- Use the generated module reference for complete member-level details.
- Use the guide pages when you want examples and workflow instead of raw API entries.
