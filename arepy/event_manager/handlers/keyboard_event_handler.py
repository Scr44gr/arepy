from ..events.keyboard_event import KeyboardPressedEvent, KeyboardReleasedEvent
from .utils import KEYS


class KeyboardEventHandler:
    def __init__(self, event_manager):
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
            if self.pressed_keys.get(event.key) is not None:
                self.pressed_keys.pop(event.key)

            self.released_keys[event.key] = True

    def is_key_pressed(self, key: str) -> bool:
        """Returns True if the key is currently pressed"""
        return self.pressed_keys.get(KEYS[key.lower()]) is not None

    def is_key_released(self, key: str) -> bool:
        """Returns True if the key is currently released"""
        return self.released_keys.get(KEYS[key.lower()]) is not None
