import pytest

from arepy.engine.animator import Animator
from arepy.engine.renderer import Color
from arepy.math.vec2 import Vec2


class ScalarTarget:
    def __init__(self, x: float = 0.0) -> None:
        self.x = x


class VectorTarget:
    def __init__(self) -> None:
        self.position = Vec2(0.0, 0.0)


class ColorTarget:
    def __init__(self) -> None:
        self.tint = Color(0, 0, 0, 255)


def test_animator_interpolates_scalar_property() -> None:
    animator = Animator()
    target = ScalarTarget()

    timeline = animator.create().to(target, "x", 10.0, 1.0).start()

    animator.tick(0.0)
    assert timeline.is_running()
    assert target.x == pytest.approx(0.0)

    animator.tick(0.5)
    assert target.x == pytest.approx(5.0)

    animator.tick(1.0)
    assert target.x == pytest.approx(10.0)
    assert timeline.is_finished()


def test_animator_wait_and_callback_steps_run_in_order() -> None:
    animator = Animator()
    calls: list[str] = []

    animator.create().call(lambda: calls.append("start")).wait(0.5).call(
        lambda: calls.append("finish")
    ).start()

    animator.tick(0.0)
    assert calls == ["start"]

    animator.tick(0.25)
    assert calls == ["start"]

    animator.tick(0.5)
    assert calls == ["start", "finish"]


def test_animator_method_step_emits_interpolated_values() -> None:
    animator = Animator()
    values: list[int] = []

    animator.create().method(values.append, 0, 10, 1.0).start()

    animator.tick(0.0)
    animator.tick(0.5)
    animator.tick(1.0)

    assert values == [0, 5, 10]


def test_animator_interpolates_vec2_and_color_values() -> None:
    animator = Animator()
    vector_target = VectorTarget()
    color_target = ColorTarget()

    animator.create().to(vector_target, "position", Vec2(10.0, 20.0), 1.0).start()
    animator.create().to(color_target, "tint", Color(255, 128, 0, 255), 1.0).start()

    animator.tick(0.5)

    assert vector_target.position == Vec2(5.0, 10.0)
    assert color_target.tint == Color(128, 64, 0, 255)


def test_property_step_captures_start_value_when_step_begins() -> None:
    animator = Animator()
    target = ScalarTarget()

    animator.create().wait(0.5).to(target, "x", 20.0, 1.0).start()

    animator.tick(0.25)
    target.x = 5.0

    animator.tick(0.5)
    assert target.x == pytest.approx(5.0)

    animator.tick(1.0)
    assert target.x == pytest.approx(12.5)


def test_cancelled_timeline_stops_progress_and_skips_completion() -> None:
    animator = Animator()
    target = ScalarTarget()
    completed: list[str] = []

    timeline = (
        animator.create()
        .to(target, "x", 10.0, 1.0)
        .on_complete(lambda: completed.append("done"))
        .start()
    )

    animator.tick(0.5)
    timeline.cancel()
    animator.tick(1.0)

    assert target.x == pytest.approx(5.0)
    assert timeline.is_cancelled()
    assert completed == []


def test_zero_duration_steps_finish_in_same_tick() -> None:
    animator = Animator()
    target = ScalarTarget()
    calls: list[str] = []

    animator.create().to(target, "x", 3.0, 0.0).call(
        lambda: calls.append("done")
    ).start()

    animator.tick(0.0)

    assert target.x == pytest.approx(3.0)
    assert calls == ["done"]


def test_timeline_cannot_be_restarted_or_mutated_after_start() -> None:
    animator = Animator()
    target = ScalarTarget()
    timeline = animator.create().to(target, "x", 1.0, 0.5)

    timeline.start()

    with pytest.raises(RuntimeError):
        timeline.start()

    with pytest.raises(RuntimeError):
        timeline.wait(0.1)


def test_timeline_created_during_tick_waits_for_next_tick() -> None:
    animator = Animator()
    target = ScalarTarget()

    def spawn_second_timeline() -> None:
        animator.create().to(target, "x", 10.0, 1.0).start()

    animator.create().call(spawn_second_timeline).start()

    animator.tick(0.0)
    assert target.x == pytest.approx(0.0)

    animator.tick(0.5)
    assert target.x == pytest.approx(5.0)
