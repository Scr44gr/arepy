from sdl2 import SDL_Keycode

from ..event_manager import Event


class KeyboardPressedEvent(Event):
    def __init__(self, key: SDL_Keycode) -> None:
        super().__init__()
        self.key: SDL_Keycode = key

    def __repr__(self) -> str:
        return f"KeyboardPressedEvent(key={self.key})"


class KeyboardReleasedEvent(Event):
    def __init__(self, key: SDL_Keycode) -> None:
        super().__init__()
        self.key: SDL_Keycode = key

    def __repr__(self) -> str:
        return f"KeyboardReleasedEvent(key={self.key})"
