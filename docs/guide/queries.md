# Queries

Queries are the main way systems select entities.

## Filter syntax

The current implementation supports three forms:

```python
Query[Entity, With[Transform, RigidBody2D]]
Query[Entity, Without[Sprite]]
Query[Entity, tuple[With[Transform], Without[Sprite]]]
```

The shape is always:

```python
Query[EntityType, FilterType]
```

- `EntityType` is usually `Entity`
- `FilterType` is `With[...]`, `Without[...]`, or a `tuple[...]` that combines both

You do not construct a `Query(...)` object by hand. Instead, you pass it as a type annotation on a system parameter:

```python
def movement_system(query: Query[Entity, With[Transform, Velocity]]) -> None:
    ...
```

At system registration time, the registry inspects these annotations and builds internal signatures for required and excluded components.

## Iteration options

### Iterate entities

```python
for entity in query:
    ...
```

### Iterate component tuples

```python
for transform, rigidbody in query.iter_components(Transform, RigidBody2D):
    ...
```

The component types you pass to `iter_components(...)` should match the `With[...]` part of the query annotation.

### Iterate entities plus components

```python
for entity, transform, rigidbody in query.iter_entities_components(
    Transform,
    RigidBody2D,
):
    ...
```

Here the first returned value is the `Entity`, and the rest follow the component types in the same order you pass them.

## Preferred hot-path style

For gameplay loops, prefer `iter_components(...)` or `iter_entities_components(...)` over repeated `entity.get_component(...)` calls. The bundled movement and render systems already follow this pattern.

## Batch queries

Use `BatchQuery[...]` for vectorized NumPy updates:

```python
def movement_system(batch: BatchQuery[Transform, RigidBody2D]) -> None:
    position = batch.vec2(Transform, "position")
    velocity = batch.vec2(RigidBody2D, "velocity")
    position.x += velocity.x
    position.y += velocity.y
```

For scalar fields that support bound storage, `bind=True` keeps one persistent
NumPy array instead of copying values and writing them back every frame:

```python
rotation = batch.scalar(
    Transform,
    "rotation",
    dtype=np.float64,
    bind=True,
)
```

Use `writeback=False` for read-only scalar views that do not support bound
storage.

## Ordering

Query iteration is deterministic: entities are yielded ordered by entity id. That makes gameplay logic, replayability, and debugging easier to reason about.

## Matching rules

A query matches an entity when:

- all required `With[...]` components are present
- none of the `Without[...]` components are present

## Example

```python
def movement_system(
    query: Query[Entity, tuple[With[Transform, RigidBody2D], Without[Frozen]]],
    renderer: Renderer2D,
) -> None:
    delta_time = renderer.get_delta_time()

    for transform, rigidbody in query.iter_components(Transform, RigidBody2D):
        transform.position.x += rigidbody.velocity.x * delta_time
        transform.position.y += rigidbody.velocity.y * delta_time
```
