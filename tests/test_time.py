import pytest

from arepy.engine.time import Time, Timers


def test_time_advance_uses_backend_absolute_time() -> None:
    time_resource = Time(10.0)

    time_resource.advance(10.25)
    time_resource.advance(10.5)

    assert time_resource.delta_seconds == pytest.approx(0.25)
    assert time_resource.elapsed_seconds == pytest.approx(0.5)
    assert time_resource.unscaled_elapsed_seconds == pytest.approx(0.5)
    assert time_resource.frame_count == 2


def test_after_timer_fires_once() -> None:
    timers = Timers()
    calls: list[str] = []

    timers.after(0.5, lambda: calls.append("done"))

    timers.tick(0.25)
    assert calls == []

    timers.tick(0.5)
    assert calls == ["done"]

    timers.tick(1.0)
    assert calls == ["done"]


def test_repeating_timer_can_be_cancelled() -> None:
    timers = Timers()
    calls: list[int] = []
    handle = timers.every(0.5, lambda: calls.append(len(calls)))

    timers.tick(0.5)
    timers.tick(1.0)
    timers.cancel(handle)
    timers.tick(1.5)

    assert calls == [0, 1]
    assert not timers.is_active(handle)


def test_cooldown_uses_current_timer_time() -> None:
    timers = Timers()

    assert timers.cooldown("fire", 0.25)
    assert not timers.cooldown("fire", 0.25)

    timers.tick(0.3)

    assert timers.cooldown("fire", 0.25)


def test_timer_created_during_tick_waits_for_next_tick() -> None:
    timers = Timers()
    calls: list[str] = []

    def outer() -> None:
        calls.append("outer")
        timers.after(0.0, lambda: calls.append("inner"))

    timers.after(0.0, outer)

    timers.tick(0.0)
    assert calls == ["outer"]

    timers.tick(0.0)
    assert calls == ["outer", "inner"]