# Arepy 🎮

[![Upload Python Package](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml)
[![codecov](https://codecov.io/gh/Scr44gr/arepy/branch/main/graph/badge.svg)](https://codecov.io/gh/Scr44gr/arepy)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Arepy** is a modern ECS (Entity Component System) game engine written in Python, featuring seamless integration with Raylib for graphics and ImGui for debugging interfaces.

## ✨ Features

- 🚀 **High-performance ECS architecture** - Optimized entity-component-system design
- 🎨 **Raylib integration** - Hardware-accelerated 2D graphics
- 🛠️ **ImGui debugging** - Real-time debugging and profiling tools
- 🔧 **Component pools** - Memory-efficient component management
- 🎯 **Query system** - Flexible entity filtering with `With`/`Without` queries
- 📦 **Easy to use** - Simple and intuitive API design
- 🏗️ **Entity builder** - Fluent interface for entity creation

## 📖 Installation

### From PyPI
```bash
pip install arepy
```

### Development Installation
```bash
git clone https://github.com/Scr44gr/arepy.git
cd arepy
pip install -e ".[testing]"
```

## 🚀 Quick Start

### Basic Example - Moving Square

Create a simple red square that moves across the screen:

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
    """System that updates entity positions based on velocity."""
    delta_time = renderer.get_delta_time()
    
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        velocity = entity.get_component(RigidBody2D).velocity
        
        # Update position
        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time

def render_system(query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D):
    """System that renders all entities with transform and rigidbody components."""
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
    game = ArepyEngine(
        title="Arepy Example",
    )
    
    # Create a world
    world = game.create_world("main_world")
    
    # Create an entity with components
    entity = (world.create_entity()
              .with_component(Transform(position=Vec2(0, 0)))
              .with_component(RigidBody2D(velocity=Vec2(50, 10)))
              .build())
    
    # Register systems
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)
    
    # Set as current world and run
    game.set_current_world("main_world")
    game.run()
```

![Demo](https://github.com/user-attachments/assets/c23a6af6-14a0-4afc-b335-7702815a7777)

## 🏗️ Core Concepts

### Entities
Entities are lightweight identifiers that represent game objects:

```python
# Create an entity
entity = world.create_entity()

# Or use the builder pattern
player = (world.create_entity()
          .with_component(Transform(position=Vec2(100, 100)))
          .with_component(PlayerController())
          .build())
```

### Components
Components are pure data containers:

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
Systems contain the game logic and operate on entities with specific components:

```python
def damage_system(query: Query[Entity, With[Health, Weapon]]):
    """System that processes combat between entities."""
    for entity in query.get_entities():
        health = entity.get_component(Health)
        weapon = entity.get_component(Weapon)
        
        # Game logic here
        if health.value <= 0:
            entity.kill()
```

### Queries
Queries allow you to filter entities based on their components:

```python
# Entities WITH specific components
Query[Entity, With[Transform, Velocity]]

# Entities WITHOUT specific components  
Query[Entity, Without[Dead]]

# Complex combinations (planned feature)
Query[Entity, With[Transform, Velocity], Without[Frozen]]
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arepy --cov-report=html

# Run specific test file
pytest tests/test_registry.py -v
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Requirements

- Python 3.10+
- Raylib 5.5.0+
- Bitarray 3.4.2+

## 🗺️ Roadmap

- [ ] **Advanced Query System** - Support for complex component combinations
- [ ] **Scene Management** - Built-in scene loading and transitions  
- [ ] **Asset Pipeline** - Better streamlined asset loading and management
- [ ] **Physics Integration** - Built-in 2D/3D physics systems
- [ ] **Audio System** - Comprehensive audio management
- [ ] **Networking** - Multiplayer game support
- [ ] **Visual Editor** - GUI editor for game development

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Raylib](https://www.raylib.com/) - Amazing C library for 2D/3D graphics
- [ImGui](https://github.com/ocornut/imgui) - Fantastic debugging interface
- [EnTT](https://github.com/skypjack/entt) - Inspiration for ECS design
- [Bevy Engine](https://github.com/bevyengine/bevy) - Inspiration for ECS Query system
- [Pikuma](https://pikuma.com/courses/cpp-2d-game-engine-development) - Educational resources :)
- [raylib-python-cffi](https://github.com/electronstudio/raylib-python-cffi) - Python bindings for Raylib
---

**Made with ❤️ by [Abrahan Gil](https://github.com/Scr44gr)**