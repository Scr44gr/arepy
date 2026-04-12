import heapq
from dataclasses import dataclass
from typing import Callable, Dict, Hashable, List, Optional


@dataclass(frozen=True, slots=True)
class TimerHandle:
    id: int


@dataclass(slots=True)
class Time:
    delta_seconds: float = 0.0
    elapsed_seconds: float = 0.0
    frame_count: int = 0
    fixed_delta_seconds: float = 1.0 / 60.0
    accumulator_seconds: float = 0.0
    time_scale: float = 1.0
    unscaled_delta_seconds: float = 0.0
    unscaled_elapsed_seconds: float = 0.0
    _last_time_seconds: float = 0.0

    def __init__(
        self,
        current_time_seconds: float,
        fixed_delta_seconds: float = 1.0 / 60.0,
        time_scale: float = 1.0,
    ) -> None:
        self.delta_seconds = 0.0
        self.elapsed_seconds = 0.0
        self.frame_count = 0
        self.fixed_delta_seconds = fixed_delta_seconds
        self.accumulator_seconds = 0.0
        self.time_scale = time_scale
        self.unscaled_delta_seconds = 0.0
        self.unscaled_elapsed_seconds = 0.0
        self._last_time_seconds = current_time_seconds

    def advance(self, current_time_seconds: float) -> None:
        unscaled_delta = max(0.0, current_time_seconds - self._last_time_seconds)
        self._last_time_seconds = current_time_seconds
        self.unscaled_delta_seconds = unscaled_delta
        self.unscaled_elapsed_seconds += unscaled_delta
        self.delta_seconds = unscaled_delta * self.time_scale
        self.elapsed_seconds += self.delta_seconds
        self.accumulator_seconds += self.delta_seconds
        self.frame_count += 1


@dataclass(order=True, slots=True)
class _TimerEntry:
    deadline_seconds: float
    handle_id: int


@dataclass(slots=True)
class _TimerState:
    callback: Callable[[], None]
    interval_seconds: Optional[float] = None


class Timers:
    __slots__ = [
        "_cooldowns",
        "_next_handle_id",
        "_now_seconds",
        "_scheduled_entries",
        "_states",
    ]

    def __init__(self) -> None:
        self._cooldowns: Dict[Hashable, float] = {}
        self._next_handle_id = 0
        self._now_seconds = 0.0
        self._scheduled_entries: List[_TimerEntry] = []
        self._states: Dict[int, _TimerState] = {}

    def after(self, delay_seconds: float, callback: Callable[[], None]) -> TimerHandle:
        self._validate_delay(delay_seconds)
        return self._schedule(delay_seconds, callback)

    def every(
        self, interval_seconds: float, callback: Callable[[], None]
    ) -> TimerHandle:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        return self._schedule(interval_seconds, callback, interval_seconds)

    def cancel(self, handle: TimerHandle) -> None:
        self._states.pop(handle.id, None)

    def is_active(self, handle: TimerHandle) -> bool:
        return handle.id in self._states

    def cooldown(self, key: Hashable, duration_seconds: float) -> bool:
        self._validate_delay(duration_seconds)
        ready_at = self._cooldowns.get(key, float("-inf"))
        if self._now_seconds < ready_at:
            return False
        self._cooldowns[key] = self._now_seconds + duration_seconds
        return True

    def clear(self) -> None:
        self._cooldowns.clear()
        self._scheduled_entries.clear()
        self._states.clear()

    def tick(self, now_seconds: float) -> None:
        self._now_seconds = max(self._now_seconds, now_seconds)
        ready_entries: List[_TimerEntry] = []
        while (
            self._scheduled_entries
            and self._scheduled_entries[0].deadline_seconds <= self._now_seconds
        ):
            ready_entries.append(heapq.heappop(self._scheduled_entries))

        for entry in ready_entries:
            state = self._states.get(entry.handle_id)
            if state is None:
                continue

            if state.interval_seconds is None:
                self._states.pop(entry.handle_id, None)

            state.callback()

            if state.interval_seconds is None or entry.handle_id not in self._states:
                continue

            self._push_entry(
                entry.handle_id,
                self._now_seconds + state.interval_seconds,
            )

    def _schedule(
        self,
        delay_seconds: float,
        callback: Callable[[], None],
        interval_seconds: Optional[float] = None,
    ) -> TimerHandle:
        if not callable(callback):
            raise TypeError("callback must be callable")

        self._next_handle_id += 1
        handle = TimerHandle(self._next_handle_id)
        self._states[handle.id] = _TimerState(
            callback=callback,
            interval_seconds=interval_seconds,
        )
        self._push_entry(handle.id, self._now_seconds + delay_seconds)
        return handle

    def _push_entry(self, handle_id: int, deadline_seconds: float) -> None:
        heapq.heappush(
            self._scheduled_entries,
            _TimerEntry(deadline_seconds=deadline_seconds, handle_id=handle_id),
        )

    def _validate_delay(self, delay_seconds: float) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be greater than or equal to 0")