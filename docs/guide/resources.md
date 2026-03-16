# Resources and Systems

Besides queries, systems can receive shared engine resources.

## How resource injection works

When the registry registers a system, it inspects the function annotations. If a parameter is a class and a resource with the same class name exists in the registry resource map, that parameter is resolved at runtime.

In practice, that means the type annotation is the lookup key. You do not pass a string like `"Renderer2D"`; you annotate the parameter with the class itself.

```python
def render_system(renderer: Renderer2D, asset_store: AssetStore) -> None:
    ...
```

When `render_system` runs, Arepy looks for resources registered under `Renderer2D` and `AssetStore` and passes those instances for you.

Tests currently verify that:

- a system can receive one resource
- a system can receive multiple resources
- resources are resolved lazily on each run
- replacing a resource instance affects later system calls

## Engine-provided resources

`ArepyEngine` registers these shared objects during initialization:

- `Display`
- `Renderer2D`
- `Renderer3D`
- `AssetStore`
- `Input`
- `ArepyEngine`
- `AudioDevice`
- `EventManager`
- `Imgui`

You can also fetch one manually with this call shape:

```python
renderer = engine.get_resource(Renderer2D)
```

The method signature is:

```python
engine.get_resource(resource_type: type[T]) -> T
```

So the argument you pass is the class object, not an instance.

## Example

```python
from arepy import Renderer2D
from arepy.asset_store import AssetStore
from arepy.bundle.components import Sprite, Transform
from arepy.ecs import Entity, Query, With


def render_system(
    query: Query[Entity, With[Transform, Sprite]],
    renderer: Renderer2D,
    asset_store: AssetStore,
) -> None:
    for transform, sprite in query.iter_components(Transform, Sprite):
        texture = asset_store.get_texture(sprite.asset_id)
        ...
```

## Custom resources

You can also add your own objects through `ArepyEngine.add_resource(...)`.

The method signatures are:

```python
engine.add_resource(resource: object) -> None
engine.get_resource(resource_type: type[T]) -> T
```

Example:

```python
class GameSettings:
    def __init__(self, difficulty: str) -> None:
        self.difficulty = difficulty


settings = GameSettings("normal")
engine.add_resource(settings)

same_settings = engine.get_resource(GameSettings)
```

The current implementation rejects primitive values and duplicate resource names. Retrieval is done with `get_resource(ResourceType)`.
