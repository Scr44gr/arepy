from typing import Tuple

from glm import vec2
from sdl2 import SDL_Rect

from arepy.ecs.components import Component


class KeyboardControlled(Component):
    def __init__(
        self,
        up_velocity: vec2 = vec2(0.0, -1.0),
        down_velocity: vec2 = vec2(0.0, 1.0),
        left_velocity: vec2 = vec2(-1.0, 0.0),
        right_velocity: vec2 = vec2(1.0, 0.0),
    ) -> None:
        self.up_velocity = up_velocity
        self.down_velocity = down_velocity
        self.left_velocity = left_velocity
        self.right_velocity = right_velocity
