# Arepy 🎮
A ECS python game engine using sdl2. (WIP) 


## Installation 📖
```bash
pip install git+https://github.com/Scr44gr/arepy.git
```

## Usage 📝

### Basic usage example 
```python
from arepy import Arepy
from arepy.ecs import Component, System


class Position(Component):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MovementSystem(System):
    def __init__(self):
        super().__init__()
        self.require_component(Position)
        self.require_component(Velocity)

    def update(self, dt: float):
        for entity in self.get_system_entities():
            position = entity.get_component(Position)
            velocity = entity.get_component(Velocity)
            position.x += velocity.x * dt
            position.y += velocity.y * dt
            print(f"Entity {entity.get_id()} position: {position.x}, {position.y}")


if __name__ == "__main__":
    game = Arepy()
    game.init()
    game.title = "My awesome game"
    game.debug = True
    # Create a entity builder
    entity_builder = game.create_entity()
    entity_builder.with_component(Position(0, 0))
    entity_builder.with_component(Velocity(1, 1))
    # Build the entity
    player = entity_builder.build()
    game.add_system(MovementSystem)
    # We assign a lambda to the on_update event to call the update method of the MovementSystem
    game.on_update = lambda: game.get_system(MovementSystem).update(game.delta_time)
    game.run()
```