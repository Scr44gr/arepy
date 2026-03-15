<p align="center">
    <img width="450" alt="image" src="https://github.com/user-attachments/assets/f597ffbc-e4b6-4610-bc00-eaa4973e7fcf" alt="Arepy Logo"/>
</p>

[![Upload Python Package](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml)
[![codecov](https://codecov.io/gh/Scr44gr/arepy/branch/main/graph/badge.svg)](https://codecov.io/gh/Scr44gr/arepy)
[![PyPI package](https://img.shields.io/pypi/v/arepy?color=%2334D058&label=pypi%20package)](https://pypi.org/project/arepy)
[![Python versions](https://img.shields.io/pypi/pyversions/arepy.svg?color=%2334D058)](https://pypi.org/project/arepy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Arepy** is a lightweight and expressive ECS game engine built in Python, designed to make building 2D games simple, fast, and enjoyable. It provides a clean API, a modern architecture, and first-class integration with Raylib and ImGui.

---

## Features

- High-performance ECS architecture optimized for games  
- Raylib integration for hardware-accelerated 2D graphics  
- ImGui debugging overlay with real-time tools  
- Memory-efficient component pools  
- Flexible query system with `With` / `Without` filters  
- Simple and intuitive API design  
- Fluent entity builder system  

---

## Installation

### From PyPI
```bash
pip install arepy
````

### Development Installation

```bash
git clone https://github.com/Scr44gr/arepy.git
cd arepy
pip install -e ".[testing]"
```

---

## Quick Start

### Basic Example – Moving Square

```python
from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline
from arepy.bundle.components import RigidBody2D, Transform
from arepy.ecs import Entities, Query, With
from arepy.math import Vec2

# Colors
WHITE = Color(255, 255, 255, 255)
RED = Color(255, 0, 0, 255)

def movement_system(query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D):
    delta_time = renderer.get_delta_time()
    
    for transform, rigidbody in query.iter_components(Transform, RigidBody2D):
        velocity = rigidbody.velocity
        
        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time

def render_system(query: Query[Entities, With[Transform]], renderer: Renderer2D):
    renderer.start_frame()
    renderer.clear(color=WHITE)
    
    for transform, in query.iter_components(Transform):
        renderer.draw_rectangle(
            Rect(transform.position.x, transform.position.y, 50, 50),
            color=RED
        )
    renderer.end_frame()

if __name__ == "__main__":
    game = ArepyEngine(title="Arepy Example")
    
    world = game.create_world("main_world")
    
    entity = (world.create_entity()
              .with_component(Transform(position=Vec2(0, 0)))
              .with_component(RigidBody2D(velocity=Vec2(50, 10)))
              .build())
    
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    
    game.set_current_world("main_world")
    game.run()
```

![Demo](https://github.com/user-attachments/assets/c23a6af6-14a0-4afc-b335-7702815a7777)

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

Systems implement game logic:

```python
def damage_system(query: Query[Entity, With[Health, Weapon]]):
    for entity, health, weapon in query.iter_entities_components(Health, Weapon):
        
        if health.value <= 0:
            entity.kill()
```

### Queries

Filter entities based on their components:

```python
Query[Entity, With[Transform, Velocity]]
Query[Entity, Without[Dead]]
Query[Entity, tuple[With[Transform, Velocity], Without[Frozen]]]
```

Use `iter_components(...)` when you only need component data in the hot path:

```python
def movement_system(
    query: Query[Entity, tuple[With[Transform, Velocity], Without[Frozen]]],
    renderer: Renderer2D,
) -> None:
    delta_time = renderer.get_delta_time()

    for transform, velocity in query.iter_components(Transform, Velocity):
        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time
```

Use `Without[...]` to exclude entities that should not be processed:

```python
def active_projectiles_system(
    query: Query[Entity, tuple[With[Transform, Velocity], Without[Destroyed]]],
) -> None:
    for transform, velocity in query.iter_components(Transform, Velocity):
        transform.position.x += velocity.x
        transform.position.y += velocity.y
```

---

## Testing

```bash
pytest                   # Run all tests
pytest --cov=arepy       # Coverage report
pytest tests/test_registry.py -v
```

## Benchmarking

```bash
uv run python benchmarks/ecs_baseline.py
uv run python benchmarks/ecs_baseline.py --entities 1000 5000 10000 --runs 10
uv run python benchmarks/ecs_baseline.py --mode detailed --entities 1000 5000 10000 --runs 10
uv run python benchmarks/ecs_baseline.py --mode view --entities 1000 5000 10000 --runs 10
```

---

## Contributing

We welcome contributions. Refer to the [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch
3. Implement your changes and tests
4. Ensure tests pass
5. Commit and push
6. Open a Pull Request

---

## Requirements

* Python 3.11+
* Raylib 5.5.0+
* Bitarray 3.4.2+

---

## Roadmap

* [ ] Advanced query system
* [ ] Scene management
* [ ] Asset pipeline improvements
* [ ] Physics integration
* [ ] Audio system
* [ ] Networking support
* [ ] Visual editor

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

* [Raylib](https://www.raylib.com/)
* [ImGui](https://github.com/ocornut/imgui)
* [EnTT](https://github.com/skypjack/entt)
* [Bevy Engine](https://github.com/bevyengine/bevy)
* [Pikuma](https://pikuma.com/courses/cpp-2d-game-engine-development)
* [raylib-python-cffi](https://github.com/electronstudio/raylib-python-cffi)

---

**Made with ❤️ by [Abrahan Gil](https://github.com/Scr44gr)**

