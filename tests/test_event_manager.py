from arepy.event_manager import Event, EventManager


class RootEvent(Event):
    pass


class FollowUpEvent(Event):
    pass


class OrderedEvent(Event):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name


def test_process_events_defers_follow_up_emits_until_next_call() -> None:
    manager = EventManager()
    calls: list[str] = []

    def on_root(_: RootEvent) -> None:
        calls.append("root")
        manager.emit(FollowUpEvent())

    def on_follow_up(_: FollowUpEvent) -> None:
        calls.append("follow_up")

    manager.subscribe(RootEvent, on_root)
    manager.subscribe(FollowUpEvent, on_follow_up)
    manager.emit(RootEvent())

    manager.process_events()
    assert calls == ["root"]

    manager.process_events()
    assert calls == ["root", "follow_up"]


def test_process_events_preserves_emit_and_subscription_order() -> None:
    manager = EventManager()
    calls: list[str] = []

    def first(event: OrderedEvent) -> None:
        calls.append(f"first:{event.name}")

    def second(event: OrderedEvent) -> None:
        calls.append(f"second:{event.name}")

    manager.subscribe(OrderedEvent, first)
    manager.subscribe(OrderedEvent, second)
    manager.emit(OrderedEvent("a"))
    manager.emit(OrderedEvent("b"))

    manager.process_events()

    assert calls == ["first:a", "second:a", "first:b", "second:b"]


def test_process_events_does_not_collapse_duplicate_emits() -> None:
    manager = EventManager()
    calls: list[str] = []

    def on_ordered(event: OrderedEvent) -> None:
        calls.append(event.name)

    manager.subscribe(OrderedEvent, on_ordered)
    repeated_event = OrderedEvent("same")
    manager.emit(repeated_event)
    manager.emit(repeated_event)

    manager.process_events()

    assert calls == ["same", "same"]