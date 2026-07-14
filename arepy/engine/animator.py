from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from operator import attrgetter
from typing import Callable, Dict, TypeAlias, cast, overload

from ..math.vec2 import Vec2
from .renderer import Color

ScalarValue: TypeAlias = int | float
InterpolatedValue: TypeAlias = ScalarValue | Vec2 | Color
TimelineCallback: TypeAlias = Callable[[], None]
EasingFunction: TypeAlias = Callable[[float], float]


def linear(progress: float) -> float:
    return progress


def ease_in_quad(progress: float) -> float:
    return progress * progress


def ease_out_quad(progress: float) -> float:
    return 1.0 - (1.0 - progress) * (1.0 - progress)


def ease_in_out_quad(progress: float) -> float:
    if progress < 0.5:
        return 2.0 * progress * progress
    return 1.0 - ((-2.0 * progress + 2.0) ** 2) * 0.5


@dataclass(frozen=True, slots=True)
class _WaitStep:
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class _CallbackStep:
    callback: TimelineCallback


@dataclass(frozen=True, slots=True)
class _PropertyStep:
    target: object
    property_name: str
    accessor: _PropertyAccessor
    end_value: InterpolatedValue
    duration_seconds: float
    easing: EasingFunction


@dataclass(frozen=True, slots=True)
class _InterpolationStep:
    duration_seconds: float
    easing: EasingFunction
    apply: Callable[[float], None]


_TimelineStep: TypeAlias = (
    _WaitStep | _CallbackStep | _PropertyStep | _InterpolationStep
)


@dataclass(frozen=True, slots=True)
class _PropertyAccessor:
    get: Callable[[object], object]
    set: Callable[[object, object], None]


_PROPERTY_ACCESSORS: dict[str, _PropertyAccessor] = {}


def _build_property_accessor(property_name: str) -> _PropertyAccessor:
    if "." in property_name:
        def get(target: object) -> object:
            return type(target).__getattribute__(target, property_name)
    else:
        getter = cast(Callable[[object], object], attrgetter(property_name))

        def get(target: object) -> object:
            return getter(target)

    def set(target: object, value: object) -> None:
        type(target).__setattr__(target, property_name, value)

    return _PropertyAccessor(get=get, set=set)


def _get_property_accessor(property_name: str) -> _PropertyAccessor:
    accessor = _PROPERTY_ACCESSORS.get(property_name)
    if accessor is not None:
        return accessor

    accessor = _build_property_accessor(property_name)
    _PROPERTY_ACCESSORS[property_name] = accessor
    return accessor


class _TimelineState(Enum):
    READY = "ready"
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Timeline:
    __slots__ = [
        "_animator",
        "_completion_callbacks",
        "_current_step_elapsed_seconds",
        "_current_step_index",
        "_current_step_started",
        "_current_timed_step",
        "_id",
        "_last_update_seconds",
        "_state",
        "_steps",
        "_total_elapsed_seconds",
    ]

    def __init__(self, animator: Animator, timeline_id: int) -> None:
        self._animator = animator
        self._completion_callbacks: list[TimelineCallback] = []
        self._current_step_elapsed_seconds = 0.0
        self._current_step_index = 0
        self._current_step_started = False
        self._current_timed_step: _InterpolationStep | None = None
        self._id = timeline_id
        self._last_update_seconds = 0.0
        self._state = _TimelineState.READY
        self._steps: list[_TimelineStep] = []
        self._total_elapsed_seconds = 0.0

    @property
    def id(self) -> int:
        return self._id

    @property
    def total_elapsed_seconds(self) -> float:
        return self._total_elapsed_seconds

    def to(
        self,
        target: object,
        property_name: str,
        end_value: InterpolatedValue,
        duration_seconds: float,
        easing: EasingFunction = linear,
    ) -> Timeline:
        self._ensure_mutable()
        self._validate_duration(duration_seconds)
        self._validate_property_name(property_name)
        self._steps.append(
            _PropertyStep(
                target=target,
                property_name=property_name,
                accessor=_get_property_accessor(property_name),
                end_value=_clone_value(end_value),
                duration_seconds=duration_seconds,
                easing=easing,
            )
        )
        return self

    @overload
    def method(
        self,
        callback: Callable[[int], None],
        start_value: int,
        end_value: int,
        duration_seconds: float,
        easing: EasingFunction = linear,
    ) -> Timeline: ...

    @overload
    def method(
        self,
        callback: Callable[[float], None],
        start_value: float | int,
        end_value: float | int,
        duration_seconds: float,
        easing: EasingFunction = linear,
    ) -> Timeline: ...

    @overload
    def method(
        self,
        callback: Callable[[Vec2], None],
        start_value: Vec2,
        end_value: Vec2,
        duration_seconds: float,
        easing: EasingFunction = linear,
    ) -> Timeline: ...

    @overload
    def method(
        self,
        callback: Callable[[Color], None],
        start_value: Color,
        end_value: Color,
        duration_seconds: float,
        easing: EasingFunction = linear,
    ) -> Timeline: ...

    def method(
        self,
        callback: (
            Callable[[int], None]
            | Callable[[float], None]
            | Callable[[Vec2], None]
            | Callable[[Color], None]
        ),
        start_value: InterpolatedValue,
        end_value: InterpolatedValue,
        duration_seconds: float,
        easing: EasingFunction = linear,
    ) -> Timeline:
        self._ensure_mutable()
        self._validate_duration(duration_seconds)

        if _is_int_value(start_value) and _is_int_value(end_value):
            self._steps.append(
                _build_int_method_step(
                    cast(Callable[[int], None], callback),
                    start_value,
                    end_value,
                    duration_seconds,
                    easing,
                )
            )
            return self

        if _is_scalar_value(start_value) and _is_scalar_value(end_value):
            self._steps.append(
                _build_float_method_step(
                    cast(Callable[[float], None], callback),
                    float(start_value),
                    float(end_value),
                    duration_seconds,
                    easing,
                )
            )
            return self

        if isinstance(start_value, Vec2) and isinstance(end_value, Vec2):
            self._steps.append(
                _build_vec2_method_step(
                    cast(Callable[[Vec2], None], callback),
                    start_value.copy(),
                    end_value.copy(),
                    duration_seconds,
                    easing,
                )
            )
            return self

        if isinstance(start_value, Color) and isinstance(end_value, Color):
            self._steps.append(
                _build_color_method_step(
                    cast(Callable[[Color], None], callback),
                    _clone_color(start_value),
                    _clone_color(end_value),
                    duration_seconds,
                    easing,
                )
            )
            return self

        raise TypeError("method steps only support scalar values, Vec2, or Color")

    def wait(self, duration_seconds: float) -> Timeline:
        self._ensure_mutable()
        self._validate_duration(duration_seconds)
        self._steps.append(_WaitStep(duration_seconds=duration_seconds))
        return self

    def call(self, callback: TimelineCallback) -> Timeline:
        self._ensure_mutable()
        self._validate_callback(callback)
        self._steps.append(_CallbackStep(callback=callback))
        return self

    def on_complete(self, callback: TimelineCallback) -> Timeline:
        self._ensure_mutable()
        self._validate_callback(callback)
        self._completion_callbacks.append(callback)
        return self

    def start(self) -> Timeline:
        self._ensure_mutable()
        if not self._steps:
            raise ValueError("Timeline must contain at least one step before start()")

        self._state = _TimelineState.RUNNING
        self._last_update_seconds = self._animator.current_time_seconds
        self._animator._register(self)
        return self

    def cancel(self) -> None:
        self._animator.cancel(self)

    def is_running(self) -> bool:
        return self._state is _TimelineState.RUNNING

    def is_finished(self) -> bool:
        return self._state is _TimelineState.FINISHED

    def is_cancelled(self) -> bool:
        return self._state is _TimelineState.CANCELLED

    def _advance(self, delta_seconds: float) -> None:
        remaining_seconds = max(0.0, delta_seconds)

        while self._state is _TimelineState.RUNNING:
            if self._current_step_index >= len(self._steps):
                self._finish()
                return

            step = self._steps[self._current_step_index]
            if isinstance(step, _CallbackStep):
                step.callback()
                if self._state is not _TimelineState.RUNNING:
                    return
                self._move_to_next_step()
                continue

            if isinstance(step, _WaitStep):
                if step.duration_seconds == 0.0:
                    self._move_to_next_step()
                    continue

                consumed_seconds = min(
                    remaining_seconds,
                    step.duration_seconds - self._current_step_elapsed_seconds,
                )
                self._current_step_elapsed_seconds += consumed_seconds
                self._total_elapsed_seconds += consumed_seconds
                remaining_seconds -= consumed_seconds

                if self._current_step_elapsed_seconds >= step.duration_seconds:
                    self._move_to_next_step()
                    continue
                return

            timed_step = self._ensure_current_timed_step(step)
            if not self._current_step_started:
                self._current_step_started = True
                if timed_step.duration_seconds == 0.0:
                    timed_step.apply(1.0)
                    self._move_to_next_step()
                    continue
                timed_step.apply(0.0)

            if remaining_seconds <= 0.0:
                return

            consumed_seconds = min(
                remaining_seconds,
                timed_step.duration_seconds - self._current_step_elapsed_seconds,
            )
            self._current_step_elapsed_seconds += consumed_seconds
            self._total_elapsed_seconds += consumed_seconds
            remaining_seconds -= consumed_seconds

            progress = self._current_step_elapsed_seconds / timed_step.duration_seconds
            timed_step.apply(progress)

            if self._current_step_elapsed_seconds >= timed_step.duration_seconds:
                self._move_to_next_step()
                continue
            return

    def _cancel(self) -> None:
        if self._state in (_TimelineState.CANCELLED, _TimelineState.FINISHED):
            return
        self._state = _TimelineState.CANCELLED
        self._animator._unregister(self._id)

    def _finish(self) -> None:
        if self._state is not _TimelineState.RUNNING:
            return

        self._state = _TimelineState.FINISHED
        self._animator._unregister(self._id)
        for callback in tuple(self._completion_callbacks):
            callback()

    def _move_to_next_step(self) -> None:
        self._current_step_index += 1
        self._current_step_elapsed_seconds = 0.0
        self._current_step_started = False
        self._current_timed_step = None

    def _ensure_current_timed_step(
        self, step: _PropertyStep | _InterpolationStep
    ) -> _InterpolationStep:
        if self._current_timed_step is not None:
            return self._current_timed_step

        if isinstance(step, _InterpolationStep):
            self._current_timed_step = step
            return step

        start_value = step.accessor.get(step.target)
        self._current_timed_step = _build_property_interpolation_step(
            target=step.target,
            accessor=step.accessor,
            start_value=start_value,
            end_value=step.end_value,
            duration_seconds=step.duration_seconds,
            easing=step.easing,
        )
        return self._current_timed_step

    def _ensure_mutable(self) -> None:
        if self._state is _TimelineState.RUNNING:
            raise RuntimeError("Timeline cannot be modified after start()")
        if self._state is _TimelineState.FINISHED:
            raise RuntimeError("Timeline has already finished")
        if self._state is _TimelineState.CANCELLED:
            raise RuntimeError("Timeline has been cancelled")

    def _validate_callback(self, callback: TimelineCallback) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")

    def _validate_duration(self, duration_seconds: float) -> None:
        if duration_seconds < 0.0:
            raise ValueError("duration_seconds must be greater than or equal to 0")

    def _validate_property_name(self, property_name: str) -> None:
        if not property_name:
            raise ValueError("property_name must not be empty")


class Animator:
    __slots__ = ["_active_timelines", "_next_timeline_id", "_now_seconds"]

    def __init__(self) -> None:
        self._active_timelines: Dict[int, Timeline] = {}
        self._next_timeline_id = 0
        self._now_seconds = 0.0

    @property
    def current_time_seconds(self) -> float:
        return self._now_seconds

    def create(self) -> Timeline:
        self._next_timeline_id += 1
        return Timeline(self, self._next_timeline_id)

    def cancel(self, timeline: Timeline) -> None:
        self._validate_owner(timeline)
        timeline._cancel()

    def is_active(self, timeline: Timeline) -> bool:
        self._validate_owner(timeline)
        return timeline.id in self._active_timelines

    def clear(self) -> None:
        for timeline in tuple(self._active_timelines.values()):
            timeline._cancel()

    def tick(self, now_seconds: float) -> None:
        self._now_seconds = max(self._now_seconds, now_seconds)
        for timeline in tuple(self._active_timelines.values()):
            delta_seconds = max(0.0, self._now_seconds - timeline._last_update_seconds)
            timeline._last_update_seconds = self._now_seconds
            timeline._advance(delta_seconds)

    def _register(self, timeline: Timeline) -> None:
        self._active_timelines[timeline.id] = timeline

    def _unregister(self, timeline_id: int) -> None:
        self._active_timelines.pop(timeline_id, None)

    def _validate_owner(self, timeline: Timeline) -> None:
        if timeline._animator is not self:
            raise ValueError("Timeline belongs to a different Animator")


def _build_property_interpolation_step(
    target: object,
    accessor: _PropertyAccessor,
    start_value: object,
    end_value: InterpolatedValue,
    duration_seconds: float,
    easing: EasingFunction,
) -> _InterpolationStep:
    if _is_int_value(start_value) and _is_int_value(end_value):
        start_int = int(start_value)
        end_int = int(end_value)

        def apply(progress: float) -> None:
            eased_progress = easing(_clamp_unit(progress))
            accessor.set(
                target,
                _interpolate_scalar(start_int, end_int, eased_progress),
            )

        return _InterpolationStep(
            duration_seconds=duration_seconds, easing=easing, apply=apply
        )

    if _is_scalar_value(start_value) and _is_scalar_value(end_value):
        start_float = float(start_value)
        end_float = float(end_value)

        def apply(progress: float) -> None:
            eased_progress = easing(_clamp_unit(progress))
            accessor.set(
                target,
                _interpolate_scalar(start_float, end_float, eased_progress),
            )

        return _InterpolationStep(
            duration_seconds=duration_seconds, easing=easing, apply=apply
        )

    if isinstance(start_value, Vec2) and isinstance(end_value, Vec2):
        start_vec2 = start_value.copy()
        end_vec2 = end_value.copy()

        def apply(progress: float) -> None:
            eased_progress = easing(_clamp_unit(progress))
            accessor.set(target, start_vec2.lerp(end_vec2, eased_progress))

        return _InterpolationStep(
            duration_seconds=duration_seconds, easing=easing, apply=apply
        )

    if isinstance(start_value, Color) and isinstance(end_value, Color):
        start_color = _clone_color(start_value)
        end_color = _clone_color(end_value)

        def apply(progress: float) -> None:
            eased_progress = easing(_clamp_unit(progress))
            accessor.set(
                target,
                _interpolate_color(start_color, end_color, eased_progress),
            )

        return _InterpolationStep(
            duration_seconds=duration_seconds, easing=easing, apply=apply
        )

    raise TypeError("property steps only support scalar values, Vec2, or Color")


def _build_int_method_step(
    callback: Callable[[int], None],
    start_value: int,
    end_value: int,
    duration_seconds: float,
    easing: EasingFunction,
) -> _InterpolationStep:
    def apply(progress: float) -> None:
        eased_progress = easing(_clamp_unit(progress))
        callback(cast(int, _interpolate_scalar(start_value, end_value, eased_progress)))

    return _InterpolationStep(
        duration_seconds=duration_seconds, easing=easing, apply=apply
    )


def _build_float_method_step(
    callback: Callable[[float], None],
    start_value: float,
    end_value: float,
    duration_seconds: float,
    easing: EasingFunction,
) -> _InterpolationStep:
    def apply(progress: float) -> None:
        eased_progress = easing(_clamp_unit(progress))
        callback(
            cast(float, _interpolate_scalar(start_value, end_value, eased_progress))
        )

    return _InterpolationStep(
        duration_seconds=duration_seconds, easing=easing, apply=apply
    )


def _build_vec2_method_step(
    callback: Callable[[Vec2], None],
    start_value: Vec2,
    end_value: Vec2,
    duration_seconds: float,
    easing: EasingFunction,
) -> _InterpolationStep:
    def apply(progress: float) -> None:
        eased_progress = easing(_clamp_unit(progress))
        callback(start_value.lerp(end_value, eased_progress))

    return _InterpolationStep(
        duration_seconds=duration_seconds, easing=easing, apply=apply
    )


def _build_color_method_step(
    callback: Callable[[Color], None],
    start_value: Color,
    end_value: Color,
    duration_seconds: float,
    easing: EasingFunction,
) -> _InterpolationStep:
    def apply(progress: float) -> None:
        eased_progress = easing(_clamp_unit(progress))
        callback(_interpolate_color(start_value, end_value, eased_progress))

    return _InterpolationStep(
        duration_seconds=duration_seconds, easing=easing, apply=apply
    )


def _clone_value(value: InterpolatedValue) -> InterpolatedValue:
    if isinstance(value, Vec2):
        return value.copy()
    if isinstance(value, Color):
        return _clone_color(value)
    return value


def _clone_color(color: Color) -> Color:
    return Color(color.r, color.g, color.b, color.a)


def _is_int_value(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_scalar_value(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clamp_unit(progress: float) -> float:
    return max(0.0, min(1.0, progress))


def _interpolate_scalar(
    start_value: int | float,
    end_value: int | float,
    progress: float,
) -> int | float:
    interpolated = (
        float(start_value) + (float(end_value) - float(start_value)) * progress
    )
    if _is_int_value(start_value) and _is_int_value(end_value):
        return int(round(interpolated))
    return interpolated


def _interpolate_color(start_value: Color, end_value: Color, progress: float) -> Color:
    return Color(
        _clamp_color_channel(
            int(round(start_value.r + (end_value.r - start_value.r) * progress))
        ),
        _clamp_color_channel(
            int(round(start_value.g + (end_value.g - start_value.g) * progress))
        ),
        _clamp_color_channel(
            int(round(start_value.b + (end_value.b - start_value.b) * progress))
        ),
        _clamp_color_channel(
            int(round(start_value.a + (end_value.a - start_value.a) * progress))
        ),
    )


def _clamp_color_channel(value: int) -> int:
    return max(0, min(255, value))
