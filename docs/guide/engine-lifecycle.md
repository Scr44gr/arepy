# Engine Lifecycle

`ArepyEngine` is the high-level entry point for creating windows, worlds, renderers, input, audio, and shared resources.

## Creating an engine

Creating an engine is usually the first thing you do. In many cases, a title and the default settings are enough to get going.

```python
engine = ArepyEngine(title="My Game")
```

The constructor signature is:

```python
ArepyEngine(
   title: str = "Arepy Engine",
   width: int = 1920 // 3,
   height: int = 1080 // 3,
   max_frame_rate: int = 800,
   fullscreen: bool = False,
   icon_path: PathLike[str] | None = None,
   window_flags: WindowFlag | None = None,
)
```

If you want more control, you can also pass:

- `title: str` sets the window title shown in the title bar
- `width: int` sets the window width in pixels when the window is created
- `height: int` sets the window height in pixels when the window is created
- `max_frame_rate: int` is passed to `Renderer2D.set_max_framerate(...)` during engine startup
- `fullscreen: bool` decides whether `Display.toggle_fullscreen()` is called right after the window opens
- `icon_path: PathLike[str] | None` is passed to `Display.set_window_icon(...)` when you want a custom window icon
- `window_flags: WindowFlag | None` is passed to `Display.set_window_state(...)` before the window is created

Here is a more explicit example:

```python
from pathlib import Path

from arepy import ArepyEngine, WindowFlag


engine = ArepyEngine(
   title="Space Garden",
   width=1280,
   height=720,
   max_frame_rate=144,
   fullscreen=False,
   icon_path=Path("assets/icon.png"),
   window_flags=WindowFlag.VSYNC_HINT,
)
```

All of these values are passed as normal Python keyword arguments when you create the engine instance.

When the engine starts, it opens the window and makes these shared services available across the app:

- `Display`
- `Time`
- `Renderer2D`
- `Renderer3D`
- `AssetStore`
- `Input`
- `ArepyEngine`
- `AudioDevice`
- `EventManager`
- `Imgui`

That lets you create a world and start adding systems without having to wire every subsystem by hand.

Each new world also starts with a local `Timers` resource.

## Worlds

A world is a named container around an ECS `Registry`.

The methods you usually call are:

```python
world = engine.create_world(name: str)
engine.set_current_world(name: str)
```

```python
engine = ArepyEngine(title="My Game")
world = engine.create_world("main")
engine.set_current_world("main")
```

`create_world(name: str)` expects the world name as a string and returns a new `World`.

`set_current_world(name: str)` also expects the world name as a string. You pass the name of a world that was already created.

`create_world(name)` creates a `World` that can see the engine's shared services, while still keeping room for world-specific resources and callbacks. That world also receives a built-in `Timers` resource, so delayed and repeating callbacks are available immediately.

## Current frame order

The runtime loop implemented in `ArepyEngine.run()` currently works like this:

1. call `on_startup()` once
2. while the window stays open:
   - process the next frame
   - apply any deferred world switch
3. call `on_shutdown()` once

Inside a frame, the order is:

1. advance `Time` from `Display.get_time()`
2. `INPUT` pipeline
3. tick the current world's `Timers`
4. tick the current world's `Animator`
5. process queued `EventManager` events
6. registry `update()`
7. `UPDATE` pipeline
8. world `on_update()` hooks
9. engine `on_update()` hook
10. process queued `EventManager` events again
11. `RENDER` pipeline
12. `RENDER_UI` pipeline
13. world `on_render()` hooks
14. engine `on_render()` hook
15. ImGui backend render
16. renderer buffer swap

## World lifecycle hooks

Besides the engine-level hooks, each world can register its own lifecycle callbacks.

```python
world = engine.create_world("main")


@world.on_startup
def load_scene() -> None:
   ...


@world.on_update
def update_hud() -> None:
   ...


@world.on_render
def draw_debug_overlay() -> None:
   ...


@world.on_shutdown
def release_scene() -> None:
   ...
```

These hooks are useful when you want a little world-specific setup or teardown without creating a dedicated ECS system for it.

- `on_startup` runs when that world becomes the current world
- `on_update` runs once per frame after the `UPDATE` pipeline
- `on_render` runs once per frame after `RENDER` and `RENDER_UI`
- `on_shutdown` runs when you leave that world or when the engine closes

`on_update` and `on_render` are optional. They are most useful for glue code, scene orchestration, UI state, or one-off world behaviors that do not fit naturally into a regular ECS system.

## Pipeline meanings

The enum currently defines these phases:

- `UPDATE`
- `RENDER`
- `INPUT`
- `PHYSICS`
- `ASYNC_UPDATE`
- `RENDER_UI`

Only the phases explicitly called by `ArepyEngine` are part of the default frame loop today. If you depend on an additional pipeline such as `PHYSICS`, you currently need to orchestrate it through your own systems or engine customization.

## World switching

`set_current_world(name)` does not switch immediately. It stores the next world name and applies the change after the current frame step. When the switch happens, the previous world receives `on_shutdown`, and the new world receives `on_startup`.
