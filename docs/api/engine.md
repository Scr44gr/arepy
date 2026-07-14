# Engine API

This page points to the objects that start the application and connect worlds
to shared services.

- `ArepyEngine` owns the window, runtime loop, global resources, and worlds.
- `SystemPipeline` chooses when a system runs.
- `SystemState` enables or disables a registered system.

## Create and run an engine

```python
from arepy import ArepyEngine


engine = ArepyEngine(
    title="My Game",
    width=960,
    height=540,
    max_frame_rate=120,
)
world = engine.create_world("main")

engine.set_current_world("main")
engine.run()
```

`set_current_world()` schedules the named world to become active. `run()`
starts the loop and applies that selection before the first frame.

## Global and world-local resources

Engine resources are global: every engine-created world can resolve them.
Built-in global resources include `Display`, `Time`, `Renderer2D`,
`Renderer3D`, `Input`, `AudioDevice`, `AssetStore`, and `EventManager`.

A world can add local state with `add_resource()`. Local resources take
precedence over global resources of the same type name:

```python
class DialogueState:
    __slots__ = ("current_line",)

    def __init__(self) -> None:
        self.current_line = 0


dialogue_world = engine.create_world("dialogue")
dialogue_world.add_resource(DialogueState())
```

Each world also owns an `Animator` and `Timers` resource. Systems registered on
`dialogue_world` can request `DialogueState`, while renderer and input services
continue to resolve from the engine.

## Pipelines and system state

Register each system in the phase where its job belongs:

```python
from arepy import ArepyEngine, Color, Renderer2D, SystemPipeline
from arepy.ecs.systems import SystemState


PIPELINE_BACKGROUND = Color(15, 20, 32, 255)


def read_controls() -> None:
    ...


def move_entities() -> None:
    ...


def render_scene(renderer: Renderer2D) -> None:
    renderer.start_frame()
    renderer.clear(PIPELINE_BACKGROUND)
    renderer.end_frame()


def render_debug_ui() -> None:
    ...


engine = ArepyEngine(title="Pipeline example")
world = engine.create_world("main")
world.add_system(SystemPipeline.INPUT, read_controls)
world.add_system(SystemPipeline.UPDATE, move_entities)
world.add_system(SystemPipeline.RENDER, render_scene)
world.add_system_with_state(
    SystemPipeline.RENDER_UI,
    render_debug_ui,
    SystemState.OFF,
)
```

The placeholder bodies keep the pipeline example runnable; replace them with
game logic. Use `world.set_system_state(...)` with the same pipeline and
function to change the debug system between `SystemState.ON` and
`SystemState.OFF`.

## Engine hooks and world hooks

Engine hooks are methods to override in an `ArepyEngine` subclass. They are for
application-wide behavior:

```python
from arepy import ArepyEngine


class Game(ArepyEngine):
    def on_startup(self) -> None:
        print("Application started")

    def on_shutdown(self) -> None:
        print("Application stopped")
```

World hooks register callbacks on one scene and can be used as decorators:

```python
@world.on_startup
def enter_level() -> None:
    print("Level entered")


@world.on_shutdown
def leave_level() -> None:
    print("Level left")
```

Use world shutdown hooks to release resources owned by that world. A switch to
another world invokes the outgoing world's shutdown callbacks; closing the
application invokes them for the active world.

## Good companion pages

- [Engine Lifecycle](../guide/engine-lifecycle.md)
- [Resources and Systems](../guide/resources.md)
- [Core Services](services.md)

## Generated modules

- [ArepyEngine module](reference/arepy/engine/engine.md)
- [Display module](reference/arepy/engine/display.md)
- [Renderer2D module](reference/arepy/engine/renderer/renderer_2d.md)
- [Renderer3D module](reference/arepy/engine/renderer/renderer_3d.md)
- [Input module](reference/arepy/engine/input.md)
- [Audio module](reference/arepy/engine/audio.md)

For the full module layout, browse **Public API**. For a guided workflow, start
with engine lifecycle and resources.
