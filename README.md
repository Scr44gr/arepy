<p align="center">
    <img width="450" alt="image" src="https://github.com/user-attachments/assets/ac97e33d-7b04-48b5-8bce-8c95d8c30a81" alt="Arepy Logo"/>
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
from arepy.bundle.components.rigidbody_component import RigidBody2D
from arepy.bundle.components.transform_component import Transform
from arepy.ecs import Entities, Query, With
from arepy.math import Vec2

# Colors
WHITE = Color(255, 255, 255, 255)
RED = Color(255, 0, 0, 255)

def movement_system(query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D):
    delta_time = renderer.get_delta_time()
    
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        velocity = entity.get_component(RigidBody2D).velocity
        
        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time

def render_system(query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D):
    renderer.start_frame()
    renderer.clear(color=WHITE)
    
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
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
```

### Components

Pure data containers attached to entities:

```python
from arepy.ecs import Component

class Health(Component):
    def __init__(self, value: int = 100):
        self.value = value
        self.max_value = value

class Weapon(Component):
    def __init__(self, damage: int = 10, range: float = 100.0):
        self.damage = damage
        self.range = range
```

### Systems

Systems implement game logic:

```python
def damage_system(query: Query[Entity, With[Health, Weapon]]):
    for entity in query.get_entities():
        health = entity.get_component(Health)
        weapon = entity.get_component(Weapon)
        
        if health.value <= 0:
            entity.kill()
```

### Queries

Filter entities based on their components:

```python
Query[Entity, With[Transform, Velocity]]
Query[Entity, Without[Dead]]

# Planned:
Query[Entity, With[Transform, Velocity], Without[Frozen]]
```

---

## Testing

```bash
pytest                   # Run all tests
pytest --cov=arepy       # Coverage report
pytest tests/test_registry.py -v
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

* Python 3.10+
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

