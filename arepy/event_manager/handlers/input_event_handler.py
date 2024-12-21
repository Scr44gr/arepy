from typing import Dict

from arepy.engine.input import Key, MouseButton

from .. import EventManager
from ..events.keyboard_event import KeyboardPressedEvent, KeyboardReleasedEvent
from ..events.mouse_event import (
    Event,
    MouseMovedEvent,
    MousePressedEvent,
    MouseReleasedEvent,
    MouseWheelEvent,
)


class ClearEvents(Event):
    def __init__(self) -> None:
        super().__init__()


class InputEventHandler:
    __slots__ = ["released_keys", "pressed_keys", "mouse_events"]

    def __init__(self, event_manager: EventManager):
        # Subscribe to the events
        event_manager.subscribe(KeyboardPressedEvent, self._on_keyboard_pressed)
        event_manager.subscribe(KeyboardReleasedEvent, self._on_keyboard_released)
        event_manager.subscribe(MouseMovedEvent, self._on_mouse_moved)
        event_manager.subscribe(MousePressedEvent, self._on_mouse_pressed)
        event_manager.subscribe(MouseReleasedEvent, self._on_mouse_released)
        event_manager.subscribe(MouseWheelEvent, self._on_mouse_wheel)
        event_manager.subscribe(ClearEvents, self._clear_events)
        self.released_keys: Dict[Key, bool] = {}
        self.pressed_keys: Dict[Key, bool] = {}
        self.mouse_events = {}

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

    def _on_mouse_moved(self, event: MouseMovedEvent):
        self.mouse_events[MouseMovedEvent] = event

    def _on_mouse_pressed(self, event: MousePressedEvent):
        self.mouse_events[MousePressedEvent] = event
        if (
            self.mouse_events.get(MouseReleasedEvent)
            and self.mouse_events[MouseReleasedEvent].button == event.button
        ):
            self.mouse_events.pop(MouseReleasedEvent)

    def _on_mouse_released(self, event: MouseReleasedEvent):
        self.mouse_events[MouseReleasedEvent] = event
        if self.mouse_events.get(MousePressedEvent) and (
            self.mouse_events[MousePressedEvent].button == event.button
        ):
            self.mouse_events.pop(MousePressedEvent)

    def _on_mouse_wheel(self, event: MouseWheelEvent):
        self.mouse_events[MouseWheelEvent] = event

    def _clear_events(self, _: ClearEvents):
        self.mouse_events = {}
        self.released_keys: Dict[Key, bool] = {}
        self.pressed_keys: Dict[Key, bool] = {}

    def is_key_pressed(self, key: Key) -> bool:
        """Returns True if the key is currently pressed"""
        return self.pressed_keys.get(key) is not None

    def is_key_released(self, key: Key) -> bool:
        """Returns True if the key is currently released"""
        released = self.released_keys.get(key) is not None
        if released:
            self.released_keys.pop(key)

        return released

    def is_key_down(self, key: Key) -> bool:
        """Returns True if the key is currently down"""
        return self.is_key_pressed(key) or self.is_key_released(key)

    def is_key_up(self, key: Key) -> bool:
        """Returns True if the key is currently up"""
        return not self.is_key_down(key)

    def get_mouse_position(self) -> tuple[float, float]:
        """Get the mouse position in the window."""
        if self.mouse_events.get(MouseMovedEvent) is None:
            return 0, 0
        mouse_position: MouseMovedEvent = self.mouse_events.get(MouseMovedEvent)  # type: ignore
        return mouse_position.x, mouse_position.y

    def is_mouse_button_pressed(self, button: MouseButton) -> bool:
        """Returns True if the mouse button is currently pressed"""
        return bool(
            self.mouse_events.get(MousePressedEvent)
            and self.mouse_events[MousePressedEvent].button == button
        )

    def is_mouse_button_released(self, button: MouseButton) -> bool:
        """Returns True if the mouse button is currently released"""
        return bool(
            self.mouse_events.get(MouseReleasedEvent)
            and self.mouse_events[MouseReleasedEvent].button == button
        )
