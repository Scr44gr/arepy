from ...engine.input import Key
from ..event_manager import Event


class KeyboardPressedEvent(Event):
    def __init__(self, key: Key) -> None:
        super().__init__()
        self.key: Key = key

    def __repr__(self) -> str:
        return f"KeyboardPressedEvent(key={self.key})"


class KeyboardReleasedEvent(Event):
    def __init__(self, key: Key) -> None:
        super().__init__()
        self.key: Key = key

    def __repr__(self) -> str:
        return f"KeyboardReleasedEvent(key={self.key})"
