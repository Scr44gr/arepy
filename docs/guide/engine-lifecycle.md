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
   width: int = 640,
   height: int = 360,
   max_frame_rate: int = 800,
   fullscreen: bool = False,
   vsync: bool = False,
   icon_path: PathLike[str] | None = None,
)
```

If you want more control, you can also pass:

- `title: str` sets the window title shown in the title bar
- `width: int` sets the window width in pixels when the window is created
- `height: int` sets the window height in pixels when the window is created
- `max_frame_rate: int` is passed to `Renderer2D.set_max_framerate(...)` during engine startup
- `fullscreen: bool` decides whether `Display.toggle_fullscreen()` is called right after the window opens
- `vsync: bool` is passed to `Display.set_vsync(...)` before the window is created
- `icon_path: PathLike[str] | None` is passed to `Display.set_window_icon(...)` when you want a custom window icon

Here is a more explicit example:

```python
from pathlib import Path

from arepy import ArepyEngine


engine = ArepyEngine(
   title="Space Garden",
   width=1280,
   height=720,
   max_frame_rate=144,
   fullscreen=False,
   vsync=True,
   icon_path=Path("assets/icon.png"),
)
```

All of these values are passed as normal Python keyword arguments when you create the engine instance.

When the engine starts, it opens the window and makes these shared services available across the app:

- `Display`
- `Renderer2D`
- `Renderer3D`
- `AssetStore`
- `Input`
- `ArepyEngine`
- `AudioDevice`
- `EventManager`
- `Imgui`

That lets you create a world and start adding systems without having to wire every subsystem by hand.

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

`create_world(name)` also copies the engine resource map into the world's registry, which is what makes typed resource injection work inside systems.

## Current frame order

The runtime loop implemented in `ArepyEngine.run()` currently works like this:

1. call `on_startup()` once
2. while the window stays open:
   - process the next frame
   - apply any deferred world switch
3. call `on_shutdown()` once

Inside a frame, the order is:

1. `INPUT` pipeline
2. registry `update()`
3. `UPDATE` pipeline
4. engine `on_update()` hook
5. `RENDER` pipeline
6. `RENDER_UI` pipeline
7. engine `on_render()` hook
8. ImGui backend render
9. renderer buffer swap

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

`set_current_world(name)` does not switch immediately. It stores the next world name and applies the change after the current frame step. This keeps switching predictable during execution.
