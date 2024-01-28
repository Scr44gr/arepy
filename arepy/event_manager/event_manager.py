from typing import Callable, Dict, List, Optional, Type, TypeVar

TEvent = TypeVar("TEvent", bound="Event")


class Event:
    class EventId:
        __id_counters: dict = {}
        __last_insert: Optional[str] = None

        @classmethod
        def get_id(cls, class_name):
            internal_class_name = f"{class_name}_{id(cls)}"
            if not internal_class_name in cls.__id_counters:
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
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}

    # subscribe
    def subscribe(
        self, event: Type[TEvent], callback: Callable[[TEvent], None]
    ) -> None:
        event_id = event.EventId.get_id(event.__name__)
        if not event_id in self._subscribers:
            self._subscribers[event_id] = []
        self._subscribers[event_id].append(callback)

    def unsubscribe(
        self, event: Type[TEvent], callback: Callable[[TEvent], None]
    ) -> None:
        event_id = event.EventId.get_id(event.__name__)
        if event_id in self._subscribers:
            self._subscribers[event_id].remove(callback)

    def emit(self, event: Event) -> None:
        event_id = event.EventId.get_id(event.__class__.__name__)
        if event_id in self._subscribers:
            for callback in self._subscribers[event_id]:
                callback(event)
