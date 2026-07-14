# ECS API

This page is a map of the ECS types used by gameplay code.

- `World` owns a registry, entities, resources, systems, and lifecycle hooks.
- `EntityBuilder` creates an entity and attaches its initial components.
- `Component` is the base type for data attached to an entity.
- `Entity` is a lightweight handle for one live entity.
- `Query`, `With`, and `Without` select matching entities for a system.

## A small, complete setup

The following program defines one component, creates one entity, and registers
one update system. It intentionally leaves rendering out so the ECS roles stay
visible:

```python
from arepy import ArepyEngine, SystemPipeline
from arepy.ecs import Component, Entity, Query, With


class Health(Component):
    __slots__ = ("value", "maximum")

    def __init__(self, value: int, maximum: int) -> None:
        self.value = value
        self.maximum = maximum


def regenerate(query: Query[Entity, With[Health]]) -> None:
    for (health,) in query.iter_components(Health):
        if health.value < health.maximum:
            health.value += 1


engine = ArepyEngine(title="ECS example")
world = engine.create_world("main")
player = world.create_entity().with_component(Health(80, 100)).build()

world.add_system(SystemPipeline.UPDATE, regenerate)
engine.set_current_world("main")
engine.run()
```

`player` is an `Entity` handle. The `Health` object lives in its component pool,
and `regenerate` receives a query prepared by the world.

## Main concepts

### `World`

Use a world as the public scene-level object. A world provides:

- `create_entity()` for an `EntityBuilder`
- `add_system()` and `add_system_with_state()` for pipeline registration
- `add_resource()` for scene-local services and state
- `on_startup`, `on_update`, `on_render`, and `on_shutdown` callbacks

World resources are checked before engine-global resources when Arepy resolves
a system parameter.

### `Entity` and `Entities`

`Entity` represents one live entity slot and generation. It is the type used in
new query annotations:

```python
Query[Entity, With[Health]]
```

`Entities` is a separate typing alias for a `set[Entity]`; it is not an entity
constructor and it does not represent one handle. Use `Entity` when iterating a
query or accepting an individual entity. Use `query.get_entities()` when code
specifically needs the matching set.

### `EntityBuilder`

`world.create_entity()` reserves an entity and returns an `EntityBuilder`.
Chain `with_component(...)` for the initial data, then call `build()` once:

```python
player = (
    world.create_entity()
    .with_component(Health(value=80, maximum=100))
    .build()
)
```

Gameplay code does not need to manipulate component pools or signatures
directly.

### `Query`, `With`, and `Without`

The filter describes membership; iteration describes the data the system needs:

```python
def damaged_entities(
    query: Query[Entity, With[Health]],
) -> None:
    for entity, health in query.iter_entities_components(Health):
        if health.value == 0:
            entity.kill()
```

Read the annotation as: "select entities that have `Health`." Add
`Without[Disabled]` in a tuple filter when a component must be absent; the
[Queries guide](../guide/queries.md) shows that form.

### Resource lookup inside systems

When a parameter is a class type such as `Renderer2D` or `GameSettings`, Arepy
resolves an instance by type name. Lookup order is:

1. resources on the current world
2. global resources owned by the engine

This keeps scene state local while shared services remain available to every
world.

## Good companion pages

- [ECS Basics](../guide/ecs.md)
- [Queries](../guide/queries.md)
- [Resources and Systems](../guide/resources.md)

## Generated modules

- [World module](reference/arepy/ecs/world.md)
- [Builders module](reference/arepy/ecs/builders.md)
- [Components module](reference/arepy/ecs/components.md)
- [Entity and Entities module](reference/arepy/ecs/entities.md)
- [Query module](reference/arepy/ecs/query/index.md)

For member-level details, continue through the generated modules in
**Public API**. Use the guide pages for workflows and explanations.
