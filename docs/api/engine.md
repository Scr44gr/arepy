# Engine API

This page points you to the main engine entry points.

- `ArepyEngine` is the main object that owns shared services and worlds.
- `SystemPipeline` helps organize the order in which systems run.
- `SystemState` stores the state object used by stateful systems.

## Start here if you want to...

- open a window and boot the engine with `ArepyEngine(...)`
- create or switch scenes with `create_world(...)` and `set_current_world(...)`
- expose shared services such as rendering, input, audio, assets, and events
- understand when engine hooks and world hooks run during a frame

## Main concepts

### `ArepyEngine`

`ArepyEngine` owns the application-level services and the runtime loop.

The most important calls are:

```python
engine = ArepyEngine(title="My Game")
world = engine.create_world("main")
engine.set_current_world("main")
engine.run()
```

Engine resources are global. They are visible from every world and include objects such as `Display`, `Renderer2D`, `Renderer3D`, `Input`, `AudioDevice`, `AssetStore`, and `EventManager`.

### Worlds managed by the engine

When you create a world through the engine, that world receives access to the engine's global resources and can also define local resources of its own.

That makes this pattern possible:

```python
class DialogueState:
	def __init__(self) -> None:
		self.current_line = 0


world = engine.create_world("dialogue")
world.add_resource(DialogueState())
```

Inside systems registered on that world, `DialogueState` resolves locally, while services such as `Renderer2D` still come from the engine.

### Engine hooks vs world hooks

`ArepyEngine` still exposes its own hooks:

- `on_startup()`
- `on_update()`
- `on_render()`
- `on_shutdown()`

In addition, each world can register:

- `world.on_startup`
- `world.on_update`
- `world.on_render`
- `world.on_shutdown`

Use engine hooks for app-wide behavior. Use world hooks for scene-specific setup, teardown, or small pieces of orchestration that belong to one world.

## Good companion pages

- [Engine Lifecycle](../guide/engine-lifecycle.md)
- [Resources and Systems](../guide/resources.md)
- [Core Services](services.md)

## Generated reference

- [ArepyEngine module](reference/arepy/engine/engine/)
- [Display module](reference/arepy/engine/display/)
- [Renderer2D module](reference/arepy/engine/renderer/renderer_2d/)
- [Renderer3D module](reference/arepy/engine/renderer/renderer_3d/)
- [Input module](reference/arepy/engine/input/)
- [Audio module](reference/arepy/engine/audio/)

## Where to keep reading

- For the full module layout, browse the generated module reference in `API Reference`.
- For a friendlier walkthrough, start with the guide pages about engine lifecycle and resources.
