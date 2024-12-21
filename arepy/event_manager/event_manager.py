from typing import Callable, Dict, List, Optional, Set, Type, TypeVar

TEvent = TypeVar("TEvent", bound="Event")


class Event:
    class EventId:
        __id_counters: Dict[str, int] = {}
        __last_insert: Optional[str] = None

        @classmethod
        def get_id(cls, class_name: str) -> int:
            internal_class_name = f"{class_name}_{id(cls)}"
            if internal_class_name not in cls.__id_counters:
                counter = 0
                if cls.__last_insert:
                    counter = cls.__id_counters[cls.__last_insert]
                cls.__id_counters[internal_class_name] = counter + 1
                cls.__last_insert = internal_class_name
            return cls.__id_counters[internal_class_name]

        def __init__(self, event_id: str) -> None:
            self.event_id = event_id

        def __repr__(self) -> str:
            return f"EventId(event_id={self.event_id})"


class EventManager:
    """A simple event manager that allows to subscribe and emit events."""

    __slots__ = ["_subscribers", "_queue_events"]

    def __init__(self) -> None:
        self._subscribers: Dict[int, List[Callable]] = {}
        self._queue_events: Set[tuple[Event, Callable[..., None]]] = set()

    def subscribe(
        self, event: Type[TEvent], callback: Callable[[TEvent], None]
    ) -> None:
        """Subscribe to an event.

        Args:
            event (Type[TEvent]): The event to subscribe.
            callback (Callable[[TEvent], None]): The callback to call when the event is emitted.
        """
        event_id = event.EventId.get_id(event.__name__)
        if event_id not in self._subscribers:
            self._subscribers[event_id] = []
        self._subscribers[event_id].append(callback)

    def unsubscribe(
        self, event: Type[TEvent], callback: Callable[[TEvent], None]
    ) -> None:
        """Unsubscribe from an event.

        Args:
            event (Type[TEvent]): The event to unsubscribe.
            callback (Callable[[TEvent], None]): The callback to remove from the subscribers.
        """
        event_id = event.EventId.get_id(event.__name__)
        if event_id in self._subscribers:
            self._subscribers[event_id].remove(callback)

    def emit(self, event: Event) -> None:
        """Emit an event."""
        event_id = event.EventId.get_id(event.__class__.__name__)
        if event_id in self._subscribers:
            for callback in self._subscribers[event_id]:
                self._queue_events.add((event, callback))

    def process_events(self) -> None:
        """Process all the events in the queue."""
        for event, callback in self._queue_events:
            callback(event)
        self._queue_events.clear()
