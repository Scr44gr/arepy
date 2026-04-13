from types import SimpleNamespace

import pytest

from arepy.engine.animator import Animator
from arepy.engine.audio import AudioDevice
from arepy.engine.display import Display
from arepy.engine.engine import ArepyEngine
from arepy.engine.input import Input
from arepy.engine.renderer.renderer_2d import Renderer2D
from arepy.engine.time import Time, Timers


class FakeDisplay:
    def __init__(self):
        self._should_close = False
        self._time_values = [0.0]
        self._last_time = 0.0

    def create_window(self, width: int, height: int, title: str) -> None:
        self.window = (width, height, title)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = True

    def set_window_state(self, flags) -> None:
        self.window_state = flags

    def set_window_icon(self, icon_path) -> None:
        self.icon_path = icon_path

    def window_should_close(self) -> bool:
        return self._should_close

    def set_time_values(self, values: list[float]) -> None:
        self._time_values = values or [self._last_time]
        self._last_time = self._time_values[-1]

    def get_time(self) -> float:
        if self._time_values:
            self._last_time = self._time_values.pop(0)
        return self._last_time


class FakeRenderer2D:
    def set_max_framerate(self, frame_rate: int) -> None:
        self.frame_rate = frame_rate

    def swap_buffers(self) -> None:
        self.swapped = True


class FakeRenderer3D:
    pass


class FakeInput:
    pass


class FakeAudioDevice:
    def init_device(self) -> None:
        self.initialized = True


class FakeImgui:
    def get_draw_data(self):
        return None


class FakeImguiBackend:
    def process_inputs(self) -> None:
        self.processed = True

    def render(self, draw_data) -> None:
        self.draw_data = draw_data


def make_fake_dependencies():
    return SimpleNamespace(
        display_repository=FakeDisplay(),
        renderer_repository=FakeRenderer2D(),
        renderer_3d_repository=FakeRenderer3D(),
        input_repository=FakeInput(),
        audio_device_repository=FakeAudioDevice(),
        imgui_repository=FakeImgui(),
        imgui_renderer_repository=lambda: FakeImguiBackend(),
    )


class TestEngineWorldLifecycle:
    def test_world_switch_triggers_startup_and_shutdown(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        first_world = engine.create_world("first")
        second_world = engine.create_world("second")
        calls: list[str] = []

        @first_world.on_startup
        def first_startup() -> None:
            calls.append("first_startup")

        @first_world.on_shutdown
        def first_shutdown() -> None:
            calls.append("first_shutdown")

        @second_world.on_startup
        def second_startup() -> None:
            calls.append("second_startup")

        engine.set_current_world("first")
        engine._ArepyEngine__check_and_set_world()
        engine.set_current_world("second")
        engine._ArepyEngine__check_and_set_world()

        assert calls == ["first_startup", "first_shutdown", "second_startup"]

    def test_world_update_and_render_hooks_run_during_frame(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        world = engine.create_world("main")
        calls: list[str] = []

        @world.on_update
        def world_update() -> None:
            calls.append("update")

        @world.on_render
        def world_render() -> None:
            calls.append("render")

        engine.set_current_world("main")
        engine._ArepyEngine__check_and_set_world()
        engine._ArepyEngine__update_process()
        engine._ArepyEngine__render_process()

        assert calls == ["update", "render"]

    def test_world_sees_global_resources_from_engine(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        world = engine.create_world("main")

        assert world.get_resource(ArepyEngine) is engine

    def test_world_system_injects_engine_protocol_resources(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        world = engine.create_world("main")
        received: dict[str, object] = {}

        def update_system(
            engine_resource: ArepyEngine,
            display: Display,
            renderer: Renderer2D,
            input_device: Input,
            audio_device: AudioDevice,
            time_resource: Time,
        ) -> None:
            received["engine"] = engine_resource
            received["display"] = display
            received["renderer"] = renderer
            received["input"] = input_device
            received["audio"] = audio_device
            received["time"] = time_resource

        from arepy.ecs.systems import SystemPipeline

        world.add_system(SystemPipeline.UPDATE, update_system)
        engine.set_current_world("main")
        engine._ArepyEngine__check_and_set_world()
        engine._ArepyEngine__update_process()

        assert received == {
            "engine": engine,
            "display": engine.display,
            "renderer": engine.renderer_2d,
            "input": engine.input,
            "audio": engine.audio_device,
            "time": engine.get_resource(Time),
        }

    def test_world_has_world_scoped_timers_resource(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        world = engine.create_world("main")

        assert isinstance(world.get_world_resource(Timers), Timers)

    def test_world_has_world_scoped_animator_resource(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        world = engine.create_world("main")

        assert isinstance(world.get_world_resource(Animator), Animator)

    def test_engine_advances_time_and_ticks_timers(self, monkeypatch):
        dependencies = make_fake_dependencies()
        dependencies.display_repository.set_time_values([10.0, 10.2, 10.6])
        monkeypatch.setattr("arepy.container.dependencies", lambda: dependencies)

        engine = ArepyEngine()
        world = engine.create_world("main")
        callbacks: list[float] = []

        world.get_world_resource(Timers).after(
            0.5,
            lambda: callbacks.append(engine.get_resource(Time).elapsed_seconds),
        )

        engine.set_current_world("main")
        engine._ArepyEngine__check_and_set_world()

        engine._ArepyEngine__next_frame()
        assert callbacks == []

        engine._ArepyEngine__next_frame()

        assert callbacks == [pytest.approx(0.6)]
        assert engine.get_resource(Time).delta_seconds == pytest.approx(0.4)
        assert engine.get_resource(Time).elapsed_seconds == pytest.approx(0.6)

    def test_engine_ticks_animator_world_resource(self, monkeypatch):
        dependencies = make_fake_dependencies()
        dependencies.display_repository.set_time_values([10.0, 10.2, 10.6])
        monkeypatch.setattr("arepy.container.dependencies", lambda: dependencies)

        engine = ArepyEngine()
        world = engine.create_world("main")

        class Target:
            def __init__(self) -> None:
                self.x = 0.0

        target = Target()
        world.get_world_resource(Animator).create().to(target, "x", 1.0, 0.5).start()

        engine.set_current_world("main")
        engine._ArepyEngine__check_and_set_world()

        engine._ArepyEngine__next_frame()
        assert target.x == pytest.approx(0.4)

        engine._ArepyEngine__next_frame()
        assert target.x == pytest.approx(1.0)
