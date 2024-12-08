# Arepy 🎮
An ECS game engine created in python with raylib and imgui integration :)

## Installation 📖
```bash
pip install git+https://github.com/Scr44gr/arepy.git
```

## Usage 📝

### Basic usage example 

#### Creating a simple system to move entities

```python
from arepy.bundle.components.rigidbody_component import RigidBody2D
from arepy.bundle.components.transform_component import Transform
from arepy.ecs.entities import Entities
from arepy.ecs.query import Query, With
from arepy.engine.renderer.renderer_2d import Renderer2D

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
```

TODO!: create a nice README.md
