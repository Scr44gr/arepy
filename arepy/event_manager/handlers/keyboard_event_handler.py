# For now we aren't using this because we have a better and simple
# way to handle keyboard events by `Input` class.
# maybe will be used in the future. so I will keep it here. :)
from ...event_manager import EventManager
from ..events.keyboard_event import KeyboardPressedEvent, KeyboardReleasedEvent
from .utils import KEYS


class KeyboardEventHandler:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.event_manager.subscribe(KeyboardPressedEvent, self._on_keyboard_pressed)
        self.event_manager.subscribe(KeyboardReleasedEvent, self._on_keyboard_released)
        self.released_keys = {}
        self.pressed_keys = {}

    def _on_keyboard_pressed(self, event: KeyboardPressedEvent):
        if self.pressed_keys.get(event.key) is None:
            self.pressed_keys[event.key] = True

        if self.released_keys.get(event.key) is not None:
            self.released_keys.pop(event.key)

    def _on_keyboard_released(self, event: KeyboardReleasedEvent):
        if self.released_keys.get(event.key) is None:
            self.released_keys[event.key] = True

        if self.pressed_keys.get(event.key) is not None:
            self.pressed_keys.pop(event.key)

    def is_key_pressed(self, key: str) -> bool:
        """Returns True if the key is currently pressed"""
        return self.pressed_keys.get(KEYS[key.lower()]) is not None

    def is_key_released(self, key: str) -> bool:
        """Returns True if the key is currently released"""
        released = self.released_keys.get(KEYS[key.lower()]) is not None
        if released:
            self.released_keys.pop(KEYS[key.lower()])

        return released
