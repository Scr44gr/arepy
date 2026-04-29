# Resources and Systems

Besides queries, systems can receive services and state objects through typed resource injection.

## How resource injection works

When the registry registers a system, it inspects the function annotations.

Most of the time, a resource is a class-based object such as `Renderer2D`, `AssetStore`, `Time`, or your own `GameSettings` object.

If a parameter is annotated with one of those class types, Arepy treats that annotation as a resource lookup.

In practice, the type annotation is the lookup key. You do not pass a string like `"Renderer2D"`; you annotate the parameter with the class itself.

```python
def render_system(renderer: Renderer2D, asset_store: AssetStore) -> None:
    ...
```

When `render_system` runs, Arepy looks for resources registered under `Renderer2D` and `AssetStore` and passes those instances for you.

This keeps system signatures readable: the function tells you what it needs, and the engine provides it.

There is one optional special case: when the `imgui` extra is installed, Arepy also registers the `imgui` module as a global resource. In beginner code, it is usually simpler to import `imgui` directly and use it normally.

## Engine-provided resources

`ArepyEngine` registers these shared objects during initialization:

- `Display`
- `Time`
- `Renderer2D`
- `Renderer3D`
- `AssetStore`
- `Input`
- `ArepyEngine`
- `AudioDevice`
- `EventManager`
- `imgui` (optional)

You can also fetch one manually with this call shape:

```python
renderer = engine.get_resource(Renderer2D)
```

And if the optional ImGui extra is installed:

```python
from arepy import imgui


imgui_module = world.get_resource(imgui)
```

In normal gameplay code, the argument you pass is usually the class object, not an instance.

## Global resources and world resources

Arepy now distinguishes between two layers of resources:

- **Global resources** live on `ArepyEngine` and are shared across every world.
- **World resources** live on a specific `World` and are only visible inside that world.

When a system asks for a resource, the lookup order is:

1. the current world's local resources
2. the engine's global resources

That means a world can override a shared service or provide scene-specific state without affecting the rest of the application.

Each world also starts with built-in local `Timers` and `Animator` resources. You do not need to register them yourself.

That makes mixed timing injection possible:

```python
from arepy import Animator, Time, Timers


def spawn_system(time: Time, timers: Timers, animator: Animator) -> None:
    if timers.cooldown("spawn", 1.0):
        print(f"spawn at {time.elapsed_seconds:.2f}s")
        animator.create().call(lambda: print("spawn flash")).start()
```

```python
class ScoreBoard:
    def __init__(self) -> None:
        self.total = 0


world = engine.create_world("main")
world.add_resource(ScoreBoard())


def hud_system(scoreboard: ScoreBoard, renderer: Renderer2D) -> None:
    ...
```

In that example, `ScoreBoard` exists only for `main`.

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

You can add your own objects either globally on the engine or locally on a world.

The most common method shapes are:

```python
engine.add_resource(resource: object) -> None
world.add_resource(resource: object) -> None
engine.get_resource(Renderer2D)
world.get_resource(GameSettings)
world.get_world_resource(DialogueState)
world.get_global_resource(Time)
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

And the world-scoped version looks like this:

```python
class DialogueState:
    def __init__(self) -> None:
        self.current_line = 0


dialogue_world = engine.create_world("dialogue")
dialogue_world.add_resource(DialogueState())

state = dialogue_world.get_world_resource(DialogueState)
```

Use engine resources for things that should exist everywhere, such as services, configuration, global managers, or shared timing state like `Time`. Use world resources for scene state, temporary controllers, and data that should disappear when that world is no longer active, including the built-in `Timers` service.
