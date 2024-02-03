from glm import vec2

from arepy.ecs.systems import System
from arepy.event_manager.handlers.keyboard_event_handler import KeyboardEventHandler

from ..components import KeyboardControlled, Rigidbody, Sprite


class PlayerMovementSystem(System):
    def __init__(self) -> None:
        super().__init__()
        self.require_components(
            [
                Sprite,
                Rigidbody,
                KeyboardControlled,
            ]
        )

    def update(self, keyboard_handler: KeyboardEventHandler, delta_time: float):
        for entity in self.get_entities():
            rigidbody = entity.get_component(Rigidbody)
            keyboard_controlled = entity.get_component(KeyboardControlled)
            sprite = entity.get_component(Sprite)

            if keyboard_handler.is_key_pressed("space"):
                rigidbody.velocity = vec2(0, 0)
                sprite.src_rect.y = 0

            if keyboard_handler.is_key_pressed("w"):
                rigidbody.velocity = keyboard_controlled.up_velocity
                sprite.src_rect.y = 0 * sprite.height

            if keyboard_handler.is_key_pressed("s"):
                rigidbody.velocity = keyboard_controlled.down_velocity
                sprite.src_rect.y = 2 * sprite.height

            if keyboard_handler.is_key_pressed("a"):
                rigidbody.velocity = keyboard_controlled.left_velocity
                sprite.src_rect.y = 3 * sprite.height

            if keyboard_handler.is_key_pressed("d"):
                rigidbody.velocity = keyboard_controlled.right_velocity
                sprite.src_rect.y = 1 * sprite.height
