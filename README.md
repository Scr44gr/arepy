<p align="center">
    <img width="450" alt="image" src="https://github.com/user-attachments/assets/f597ffbc-e4b6-4610-bc00-eaa4973e7fcf" alt="Arepy Logo"/>
</p>

[![CI](https://github.com/Scr44gr/arepy/actions/workflows/ci.yml/badge.svg)](https://github.com/Scr44gr/arepy/actions/workflows/ci.yml)
[![Docs](https://github.com/Scr44gr/arepy/actions/workflows/docs.yml/badge.svg)](https://github.com/Scr44gr/arepy/actions/workflows/docs.yml)
[![Upload Python Package](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml)
[![codecov](https://codecov.io/gh/Scr44gr/arepy/branch/main/graph/badge.svg)](https://codecov.io/gh/Scr44gr/arepy)
[![PyPI package](https://img.shields.io/pypi/v/arepy?color=%2334D058&label=pypi%20package)](https://pypi.org/project/arepy)
[![Python versions](https://img.shields.io/pypi/pyversions/arepy.svg?color=%2334D058)](https://pypi.org/project/arepy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Arepy is a lightweight ECS game engine for Python focused on making game code simple to read, easy to extend, and pleasant to iterate on.

It gives you a small but practical set of engine services out of the box: worlds, typed resource injection, 2D and 3D rendering through Raylib, built-in timers and animation helpers, and optional Dear ImGui integration for tools and debug UI.

---

## Features

- ECS architecture built for gameplay code
- Typed resource injection for engine services and your own state objects
- Raylib-backed 2D and 3D rendering
- World-local `Timers` and `Animator` services
- Optional Dear ImGui integration for tools, debug panels, and quick editors
- Query filters with `With[...]` and `Without[...]`
- Fluent entity builder API

---

## Installation

### From PyPI

```bash
pip install arepy
```

If you also want Dear ImGui support:

```bash
pip install "arepy[imgui]"
```

### Local setup with `uv`

```bash
git clone https://github.com/Scr44gr/arepy.git
cd arepy
uv sync --extra docs
```

If you also want the optional ImGui extra:

```bash
uv sync --extra docs --extra imgui
```

---

## Quick Start

This example creates a small world with one moving square.

```python
from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline, Time
from arepy.bundle.components import RigidBody2D, Transform
from arepy.ecs import Entity, Query, With
from arepy.math import Vec2

WHITE = Color(255, 255, 255, 255)
RED = Color(255, 0, 0, 255)


def movement_system(
    query: Query[Entity, With[Transform, RigidBody2D]],
    time: Time,
) -> None:
    for transform, rigid_body in query.iter_components(Transform, RigidBody2D):
        transform.position.x += rigid_body.velocity.x * time.delta_seconds
        transform.position.y += rigid_body.velocity.y * time.delta_seconds


def render_system(
    query: Query[Entity, With[Transform]],
    renderer: Renderer2D,
) -> None:
    renderer.start_frame()
    renderer.clear(color=WHITE)

    for transform, in query.iter_components(Transform):
        renderer.draw_rectangle(
            Rect(transform.position.x, transform.position.y, 32, 32),
            RED,
        )

    renderer.end_frame()


def main() -> None:
    engine = ArepyEngine(title="Arepy Quickstart", width=960, height=540)
    world = engine.create_world("main")

    world.create_entity().with_component(
        Transform(position=Vec2(40, 40))
    ).with_component(
        RigidBody2D(velocity=Vec2(90, 60))
    ).build()

    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    engine.set_current_world("main")
    engine.run()


if __name__ == "__main__":
    main()
```

![Demo](https://github.com/user-attachments/assets/c23a6af6-14a0-4afc-b335-7702815a7777)

---

## Optional ImGui

If you install the `imgui` extra, Arepy exposes the real `imgui` module directly.

Use ImGui code inside `SystemPipeline.RENDER_UI` and let the engine handle the frame lifecycle.

```python
from arepy import Display, SystemPipeline, imgui


def debug_ui(display: Display) -> None:
    is_open, _ = imgui.begin("Debug")
    if is_open:
        imgui.text("Hello from Arepy")
        if imgui.button("Rename window"):
            display.set_window_title("Debug")
    imgui.end()


world.add_system(SystemPipeline.RENDER_UI, debug_ui)
```

You do not need a wrapper class.
You do not need to call `imgui.new_frame()` yourself.
You do not need to call `imgui.render()` yourself.

See [docs/guide/imgui.md](docs/guide/imgui.md) and [examples/imgui_minimal.py](examples/imgui_minimal.py) for the full workflow.

---

## Core Concepts

### Entities

Lightweight identifiers that represent objects in the game world:

```python
entity = world.create_entity()

player = (world.create_entity()
          .with_component(Transform(position=Vec2(100, 100)))
          .with_component(PlayerController())
          .build())

empty_entity = world.create_entity().build()
```

### Components

Pure data containers attached to entities:

```python
from arepy.ecs import Component

class Health(Component):
    def __init__(self, value: int = 100):
        super().__init__()
        self.value = value
        self.max_value = value

class Weapon(Component):
    def __init__(self, damage: int = 10, range: float = 100.0):
        super().__init__()
        self.damage = damage
        self.range = range
```

### Systems

Systems are plain functions. Their parameters describe what they need.

```python
def damage_system(query: Query[Entity, With[Health, Weapon]]):
    for entity, health, weapon in query.iter_entities_components(Health, Weapon):
        if health.value <= 0:
            entity.kill()
```

### Queries

Queries filter entities by component shape:

```python
Query[Entity, With[Transform, Velocity]]
Query[Entity, Without[Dead]]
Query[Entity, tuple[With[Transform, Velocity], Without[Frozen]]]
```

Use `iter_components(...)` when you only need the component data:

```python
def movement_system(
    query: Query[Entity, tuple[With[Transform, Velocity], Without[Frozen]]],
    time: Time,
) -> None:
    for transform, velocity in query.iter_components(Transform, Velocity):
        transform.position.x += velocity.x * time.delta_seconds
        transform.position.y += velocity.y * time.delta_seconds
```

### Resources

Arepy can inject shared services like `Renderer2D`, `Display`, `Time`, `Input`, `AssetStore`, and your own resource objects directly into systems.

```python
def hud_system(renderer: Renderer2D, time: Time) -> None:
    ...
```

That keeps function signatures explicit and avoids manual service lookup in most code.

### Texture Atlas Batch Rendering

If you want sprite rendering to go through the atlas path, first pack the loaded textures once:

```python
asset_store.load_texture(renderer, "bunny", "./assets/bunny.png")
texture_atlas = asset_store.build_texture_atlas(renderer)
```

Then build a batch layout from your `Sprite` list and submit it with the position views you already use in `BatchQuery`:

```python
position = batch.vec2(Transform, "position")
sprites = batch.components(Sprite)
layout = texture_atlas.get_batch_layout(sprites)
renderer.draw_texture_batch(texture_atlas, layout, position.x, position.y, WHITE)
```

`draw_texture_batch(...)` requires at least one atlas page. If the optional native `arepy_renderer` module is installed, the renderer uses it automatically; otherwise it falls back to the Python path.

---

## Learn More

- [docs/getting-started/installation.md](docs/getting-started/installation.md)
- [docs/guide/engine-lifecycle.md](docs/guide/engine-lifecycle.md)
- [docs/guide/engine-services.md](docs/guide/engine-services.md)
- [docs/guide/resources.md](docs/guide/resources.md)
- [docs/guide/imgui.md](docs/guide/imgui.md)
- [docs/guide/bundle.md](docs/guide/bundle.md)
- [examples/imgui_minimal.py](examples/imgui_minimal.py)
- [examples/bunnymark.py](examples/bunnymark.py)
- [examples/cubemark_3d.py](examples/cubemark_3d.py)

---

## Testing

```bash
uv run pytest -q
```

To run the focused engine tests:

```bash
uv run pytest tests/test_engine_worlds.py tests/test_animator.py -q
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor workflow.

---

## Requirements

- Python 3.11+
- Raylib 5.5.0+
- Bitarray 3.8.1

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

---

## Acknowledgments

- [Raylib](https://www.raylib.com/)
- [ImGui](https://github.com/ocornut/imgui)
- [EnTT](https://github.com/skypjack/entt)
- [Bevy Engine](https://github.com/bevyengine/bevy)
- [Pikuma](https://pikuma.com/courses/cpp-2d-game-engine-development)
- [raylib-python-cffi](https://github.com/electronstudio/raylib-python-cffi)

