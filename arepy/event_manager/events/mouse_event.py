from ...engine.input import MouseButton
from ..event_manager import Event


class MousePressedEvent(Event):
    __slots__ = ["button"]

    def __init__(self, button: MouseButton) -> None:
        super().__init__()
        self.button: MouseButton = button

    def __repr__(self) -> str:
        return f"MousePressedEvent(button={self.button})"


class MouseReleasedEvent(Event):
    __slots__ = ["button"]

    def __init__(self, button: MouseButton) -> None:
        super().__init__()
        self.button: MouseButton = button

    def __repr__(self) -> str:
        return f"MouseReleasedEvent(button={self.button})"


class MouseWheelEvent(Event):
    __slots__ = ["x_offset", "y_offset"]

    def __init__(self, x_offset: float, y_offset: float) -> None:
        super().__init__()
        self.x_offset: float = x_offset
        self.y_offset: float = y_offset

    def __repr__(self) -> str:
        return f"MouseWheelEvent(x_offset={self.x_offset}, y_offset={self.y_offset})"


class MouseMovedEvent(Event):
    __slots__ = ["x", "y"]

    def __init__(self, x: float, y: float) -> None:
        super().__init__()
        self.x: float = x
        self.y: float = y

    def __repr__(self) -> str:
        return f"MouseMovedEvent(x={self.x}, y={self.y})"
