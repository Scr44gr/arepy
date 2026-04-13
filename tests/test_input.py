import pytest

from arepy import GamepadAxis, GamepadButton, GamepadDeviceType
from arepy.engine.integrations.raylib.input import input_repository


class FakeRaylib:
    def __init__(self):
        self.available = {0, 2}
        self.names = {
            0: "Xbox Wireless Controller",
            1: "DualSense Wireless Controller",
            2: "Nintendo Switch Pro Controller",
            3: "Arcade Board",
        }
        self.button_state = {
            "pressed": {(2, GamepadButton.FACE_DOWN.value): True},
            "down": {(2, GamepadButton.LEFT_SHOULDER.value): True},
            "released": {(2, GamepadButton.START.value): True},
            "up": {(2, GamepadButton.RIGHT_STICK.value): True},
        }
        self.axis_counts = {0: 6, 2: 4}
        self.axis_values = {
            (2, GamepadAxis.LEFT_X.value): 0.5,
            (2, GamepadAxis.RIGHT_TRIGGER.value): -0.25,
        }
        self.vibration_calls: list[tuple[int, float, float, float]] = []

    def IsGamepadAvailable(self, gamepad_id: int) -> bool:
        return gamepad_id in self.available

    def GetGamepadName(self, gamepad_id: int) -> str | None:
        return self.names.get(gamepad_id)

    def GetGamepadAxisCount(self, gamepad_id: int) -> int:
        return self.axis_counts.get(gamepad_id, 0)

    def IsGamepadButtonPressed(self, gamepad_id: int, button: int) -> bool:
        return self.button_state["pressed"].get((gamepad_id, button), False)

    def IsGamepadButtonDown(self, gamepad_id: int, button: int) -> bool:
        return self.button_state["down"].get((gamepad_id, button), False)

    def IsGamepadButtonReleased(self, gamepad_id: int, button: int) -> bool:
        return self.button_state["released"].get((gamepad_id, button), False)

    def IsGamepadButtonUp(self, gamepad_id: int, button: int) -> bool:
        return self.button_state["up"].get((gamepad_id, button), False)

    def GetGamepadAxisMovement(self, gamepad_id: int, axis: int) -> float:
        return self.axis_values.get((gamepad_id, axis), 0.0)

    def SetGamepadVibration(
        self,
        gamepad_id: int,
        left_motor: float,
        right_motor: float,
        duration_seconds: float,
    ) -> None:
        self.vibration_calls.append(
            (gamepad_id, left_motor, right_motor, duration_seconds)
        )


class FakeFFI:
    NULL = object()

    def callback(self, _signature: str):
        def decorator(function):
            return function

        return decorator

    def string(self, value: bytes) -> bytes:
        return value


class ProbeRaylib(FakeRaylib):
    def __init__(self, warning_message: bytes | None):
        super().__init__()
        self.ffi = FakeFFI()
        self.warning_message = warning_message
        self.trace_log_callback = None

    def SetTraceLogCallback(self, callback) -> None:
        if callback is self.ffi.NULL:
            self.trace_log_callback = None
            return
        self.trace_log_callback = callback

    def SetGamepadVibration(
        self,
        gamepad_id: int,
        left_motor: float,
        right_motor: float,
        duration_seconds: float,
    ) -> None:
        if duration_seconds == 0.0 and self.trace_log_callback is not None:
            if self.warning_message is not None:
                self.trace_log_callback(4, self.warning_message, None)
            return

        super().SetGamepadVibration(
            gamepad_id,
            left_motor,
            right_motor,
            duration_seconds,
        )


def test_gamepad_types_are_exported_from_public_api() -> None:
    assert GamepadButton.FACE_DOWN.value == 7
    assert GamepadAxis.LEFT_X.value == 0
    assert GamepadDeviceType.PLAYSTATION.value == "playstation"


def test_get_available_gamepads_returns_connected_slots(monkeypatch) -> None:
    fake_rl = FakeRaylib()

    monkeypatch.setattr(input_repository, "rl", fake_rl)

    assert input_repository.get_available_gamepads() == (0, 2)


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        ("Xbox Wireless Controller", GamepadDeviceType.XBOX),
        ("DualSense Wireless Controller", GamepadDeviceType.PLAYSTATION),
        ("Wireless Controller", GamepadDeviceType.PLAYSTATION),
        ("Nintendo Switch Pro Controller", GamepadDeviceType.NINTENDO),
        ("Arcade Board", GamepadDeviceType.GENERIC),
        (None, GamepadDeviceType.UNKNOWN),
    ],
)
def test_get_gamepad_device_type_detects_common_families(
    monkeypatch, name: str | None, expected_type: GamepadDeviceType
) -> None:
    fake_rl = FakeRaylib()
    fake_rl.available = {0} if name is not None else set()
    fake_rl.names = {0: name} if name is not None else {}

    monkeypatch.setattr(input_repository, "rl", fake_rl)

    assert input_repository.get_gamepad_device_type(0) is expected_type


def test_get_gamepad_name_returns_none_when_slot_is_unavailable(monkeypatch) -> None:
    fake_rl = FakeRaylib()
    fake_rl.available = set()

    monkeypatch.setattr(input_repository, "rl", fake_rl)

    assert input_repository.get_gamepad_name(1) is None
    assert input_repository.get_gamepad_axis_count(1) == 0
    assert input_repository.get_gamepad_axis_movement(GamepadAxis.LEFT_X, 1) == 0.0


def test_gamepad_button_and_axis_queries_delegate_to_raylib(monkeypatch) -> None:
    fake_rl = FakeRaylib()

    monkeypatch.setattr(input_repository, "rl", fake_rl)

    assert input_repository.is_gamepad_button_pressed(GamepadButton.FACE_DOWN, 2)
    assert input_repository.is_gamepad_button_down(GamepadButton.LEFT_SHOULDER, 2)
    assert input_repository.is_gamepad_button_released(GamepadButton.START, 2)
    assert input_repository.is_gamepad_button_up(GamepadButton.RIGHT_STICK, 2)
    assert input_repository.get_gamepad_axis_count(2) == 4
    assert input_repository.get_gamepad_axis_movement(GamepadAxis.LEFT_X, 2) == 0.5
    assert input_repository.get_gamepad_axis_movement(
        GamepadAxis.RIGHT_TRIGGER, 2
    ) == -0.25


def test_is_gamepad_vibration_supported_checks_backend_and_slot(monkeypatch) -> None:
    fake_rl = FakeRaylib()

    monkeypatch.setattr(input_repository, "rl", fake_rl)
    monkeypatch.setattr(
        input_repository,
        "_is_gamepad_vibration_backend_supported",
        lambda: True,
    )

    assert input_repository.is_gamepad_vibration_supported(2)
    assert not input_repository.is_gamepad_vibration_supported(1)


def test_gamepad_vibration_probe_detects_stub_backend(monkeypatch) -> None:
    fake_rl = ProbeRaylib(b"GamepadSetVibration() not available on target platform")

    monkeypatch.setattr(input_repository, "rl", fake_rl)
    monkeypatch.setattr(input_repository, "_gamepad_vibration_support_cache", None)

    assert not input_repository._is_gamepad_vibration_backend_supported()


def test_set_gamepad_vibration_is_noop_when_backend_disables_it(monkeypatch) -> None:
    fake_rl = FakeRaylib()

    monkeypatch.setattr(input_repository, "rl", fake_rl)
    monkeypatch.setattr(
        input_repository,
        "_is_gamepad_vibration_backend_supported",
        lambda: False,
    )

    input_repository.set_gamepad_vibration(0.5, 0.5, 0.1, 2)

    assert fake_rl.vibration_calls == []


def test_set_gamepad_vibration_clamps_and_delegates_to_raylib(monkeypatch) -> None:
    fake_rl = FakeRaylib()

    monkeypatch.setattr(input_repository, "rl", fake_rl)

    input_repository.set_gamepad_vibration(1.7, -0.5, -2.0, 2)

    assert fake_rl.vibration_calls == [(2, 1.0, 0.0, 0.0)]


def test_set_gamepad_vibration_is_noop_for_unavailable_slots(monkeypatch) -> None:
    fake_rl = FakeRaylib()
    fake_rl.available = set()

    monkeypatch.setattr(input_repository, "rl", fake_rl)
    monkeypatch.setattr(
        input_repository,
        "_is_gamepad_vibration_backend_supported",
        lambda: True,
    )

    input_repository.set_gamepad_vibration(0.5, 0.5, 0.1, 1)

    assert fake_rl.vibration_calls == []


def test_get_gamepad_name_decodes_backend_bytes(monkeypatch) -> None:
    fake_rl = FakeRaylib()
    fake_rl.available = {0}
    fake_rl.names = {0: b"Xbox Elite Controller"}

    monkeypatch.setattr(input_repository, "rl", fake_rl)

    assert input_repository.get_gamepad_name(0) == "Xbox Elite Controller"