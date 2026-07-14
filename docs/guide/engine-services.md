# Engine services at a glance

Systems usually need more than components. They need time, input, rendering,
audio, assets, or shared game state. Arepy makes those objects available as
typed resources, so a function's parameters explain its dependencies.

```python
def pause_menu(
    input_device: Input,
    audio: AudioDevice,
    time: Time,
) -> None:
    ...
```

There is no service locator call inside the system and no setup on every
frame. Arepy resolves the arguments when the system runs.

## The services you will use first

| Service | What it answers | Learn more |
| --- | --- | --- |
| `Time` | How long was the frame? How long has the game run? | [Lifecycle](engine-lifecycle.md) |
| `Input` | Which keys, buttons, sticks, or mouse actions are active? | [Input](input.md) |
| `Renderer2D` | What should be drawn in this frame? | [2D graphics](graphics.md) |
| `AssetStore` | Where is the already-loaded texture, sound, or model? | [2D graphics](graphics.md) |
| `AudioDevice` | Play and control sounds or music. | [Audio](audio.md) |
| `Display` | Window size, title, fullscreen, cursor, and monitors. | [Engine API](../api/engine.md) |
| `Renderer3D` | Draw models, meshes, billboards, and 3D primitives. | [Built-in bundle](bundle.md) |
| `EventManager` | Queue messages between otherwise independent features. | [Resources](resources.md) |
| `imgui` | Build optional development panels. | [ImGui](imgui.md) |

## Time

Use the global `Time` resource for frame-independent gameplay:

```python
def movement_system(
    query: Query[Entity, With[Transform, RigidBody2D]],
    time: Time,
) -> None:
    for transform, body in query.iter_components(Transform, RigidBody2D):
        transform.position.x += body.velocity.x * time.delta_seconds
        transform.position.y += body.velocity.y * time.delta_seconds
```

`delta_seconds` is the elapsed game time for this frame. `elapsed_seconds` is
the accumulated game time. `time_scale` lets slow motion or pausing affect the
world-local timers and animator as well.

## Timers

Every world owns a `Timers` resource. Use it for a delayed callback, a repeated
action, or a cooldown without comparing timestamps in several systems.

```python
from arepy import Timers


def weapon_system(timers: Timers) -> None:
    if timers.cooldown("player.fire", 0.20):
        fire_projectile()
```

For setup-time scheduling:

```python
@world.on_startup
def schedule_wave() -> None:
    timers = world.get_world_resource(Timers)
    timers.after(1.0, spawn_first_wave)
    timers.every(5.0, spawn_next_wave)
```

Timer names should describe ownership (`"player.fire"`, `"level.next_wave"`)
to avoid accidental collisions inside a world.

## Animator

Every world also owns one `Animator`. It is useful for small scripted
transitions, not a replacement for a full skeletal animation tool.

```python
@world.on_startup
def fade_in() -> None:
    animator = world.get_world_resource(Animator)
    (
        animator.create()
        .to(hud_state, "opacity", 255, 0.35)
        .call(show_ready_message)
        .start()
    )
```

Property access is prepared when the timeline is built. Keep timeline creation
out of per-entity hot loops; start a timeline in response to an actual event.

## Display

`Display` controls the window rather than drawing its contents:

```python
def toggle_fullscreen(input_device: Input, display: Display) -> None:
    if input_device.is_key_pressed(Key.F11):
        display.toggle_fullscreen()
```

Window creation flags, such as VSync and resizability, are passed to
`ArepyEngine`:

```python
engine = ArepyEngine(
    title="My game",
    width=1280,
    height=720,
    window_flags=(
        WindowFlag.VSYNC_HINT | WindowFlag.WINDOW_RESIZABLE
    ),
)
```

## Global or world-local?

Renderer, input, audio, assets, display, time, engine, and events are global:
all worlds can use the same instance. Timers, animator, and your scene state are
usually world-local. A world-local resource with the same type takes precedence
for systems in that world.

Read [Resources and systems](resources.md) for custom state and ownership.
