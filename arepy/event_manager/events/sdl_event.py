from sdl2 import SDL_Event

from ...ecs.registry import Entity
from ..event_manager import Event


class SDLEvent(Event):
    """SDL event"""

    def __init__(self, event: SDL_Event):
        super().__init__()
        self.event = event
