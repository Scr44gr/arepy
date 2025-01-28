# Arepy 🎮
[![Upload Python Package](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Scr44gr/arepy/actions/workflows/python-publish.yml)

An ECS game engine created in python with raylib and imgui integration :)
## Installation 📖
```bash
pip install arepy
```

## Usage 📝

### Basic usage example 

#### Creating a simple square that moves to the right

```python
from arepy import ArepyEngine, Color, Rect, Renderer2D, SystemPipeline
from arepy.bundle.components.rigidbody_component import RigidBody2D
from arepy.bundle.components.transform_component import Transform
from arepy.ecs import Entities, Query, With
from arepy.math import Vec2

WHITE_COLOR = Color(255, 255, 255, 255)
RED_COLOR = Color(255, 0, 0, 255)


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D
):
    delta_time = renderer.get_delta_time()
    entities = query.get_entities()
    for entity in entities:
        transform = entity.get_component(Transform)
        velocity = entity.get_component(RigidBody2D).velocity

        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time


def render_system(
    query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D
):
    renderer.start_frame()
    renderer.clear(color=WHITE_COLOR)
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        renderer.draw_rectangle(
            Rect(transform.position.x, transform.position.y, 50, 50),
            color=RED_COLOR,
        )
    renderer.end_frame()


if __name__ == "__main__":
    game = ArepyEngine()
    game.title = "Example :p"
    game.init()
    # Add world to the game engine
    world = game.create_world("example_world")
    # spawn some entities

    entity = world.create_entity()
    entity.with_component(Transform(position=Vec2(0, 0))).with_component(RigidBody2D(velocity=Vec2(50, 10))).build()

    # Add systems to the world
    world.add_system(SystemPipeline.UPDATE, movement_system)
    world.add_system(SystemPipeline.RENDER, render_system)

    # Add set the world as the current world to the game engine
    game.set_current_world("example_world")
    game.run()
```

TODO!: create a nice README.md
