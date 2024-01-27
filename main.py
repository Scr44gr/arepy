from arepy import Arepy
from arepy.ecs.components import Component
from arepy.ecs.systems import System


class Position(Component):
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Health(Component):
    hp: int


class MovementSystem(System):
    def __init__(self) -> None:
        self.require_component(Position)
        self.require_component(Velocity)

    def update(self, delta_time: float):
        ...


class MyGame(Arepy):
    title: str = "My Game"
    screen_width: int = 640
    screen_height: int = 480
    max_frame_rate: int = 60
    debug: bool = True

    def setup(self):
        # init engine
        self.init()
        # Player Creation
        entity_builder = self.create_entity()
        entity_builder.with_component(Position(x=0, y=0))
        entity_builder.with_component(Velocity(x=0, y=0))
        entity_builder.with_component(Health(hp=100))
        player = entity_builder.build()

    def level(self, level: int):
        print(f"Level: {level}")

    def on_startup(self):
        ...

    def on_shutdown(self):
        ...

    def on_update(self):
        ...

    def on_render(self):
        ...


if __name__ == "__main__":
    arepy = MyGame()
    arepy.setup()
    arepy.run()
