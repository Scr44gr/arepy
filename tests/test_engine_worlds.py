from types import ModuleType, SimpleNamespace

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
    def __init__(self) -> None:
        self.new_frame_calls = 0
        self.render_calls = 0

    def new_frame(self) -> None:
        self.new_frame_calls += 1

    def render(self) -> None:
        self.render_calls += 1

    def get_draw_data(self):
        return "draw-data"


class FakeImguiBackend:
    def __init__(self) -> None:
        self.processed = False
        self.draw_data = None

    def process_inputs(self) -> None:
        self.processed = True

    def render(self, draw_data) -> None:
        self.draw_data = draw_data


def make_fake_imgui_module(name: str = "fake_imgui_module") -> ModuleType:
    module = ModuleType(name)
    module.new_frame_calls = 0
    module.render_calls = 0

    def new_frame() -> None:
        module.new_frame_calls += 1

    def render() -> None:
        module.render_calls += 1

    def get_draw_data():
        return "module-draw-data"

    module.new_frame = new_frame
    module.render = render
    module.get_draw_data = get_draw_data
    return module


def make_fake_dependencies(with_imgui: bool = True):
    imgui = FakeImgui() if with_imgui else None
    imgui_backend_factory = (lambda: FakeImguiBackend()) if with_imgui else None
    return SimpleNamespace(
        display_repository=FakeDisplay(),
        renderer_repository=FakeRenderer2D(),
        renderer_3d_repository=FakeRenderer3D(),
        input_repository=FakeInput(),
        audio_device_repository=FakeAudioDevice(),
        imgui_module=imgui,
        imgui_backend_factory=imgui_backend_factory,
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
        assert engine.imgui.new_frame_calls == 1
        assert engine.imgui.render_calls == 1
        assert engine.imgui_backend.draw_data == "draw-data"

    def test_engine_render_process_skips_imgui_when_optional_extra_missing(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies(False)
        )

        engine = ArepyEngine()
        world = engine.create_world("main")

        @world.on_render
        def world_render() -> None:
            pass

        engine.set_current_world("main")
        engine._ArepyEngine__check_and_set_world()
        engine._ArepyEngine__input_process()
        engine._ArepyEngine__render_process()

        assert engine.imgui is None
        assert engine.imgui_backend is None
        assert engine.renderer_2d.swapped is True

    def test_world_sees_global_resources_from_engine(self, monkeypatch):
        monkeypatch.setattr(
            "arepy.container.dependencies", lambda: make_fake_dependencies()
        )

        engine = ArepyEngine()
        world = engine.create_world("main")

        assert world.get_resource(ArepyEngine) is engine

    def test_world_can_inject_imgui_module_resource(self, monkeypatch):
        fake_imgui_module = make_fake_imgui_module()
        dependencies = SimpleNamespace(
            display_repository=FakeDisplay(),
            renderer_repository=FakeRenderer2D(),
            renderer_3d_repository=FakeRenderer3D(),
            input_repository=FakeInput(),
            audio_device_repository=FakeAudioDevice(),
            imgui_module=fake_imgui_module,
            imgui_backend_factory=lambda: FakeImguiBackend(),
        )
        monkeypatch.setattr("arepy.container.dependencies", lambda: dependencies)

        engine = ArepyEngine()
        world = engine.create_world("main")
        received: dict[str, object] = {}

        def ui_system(imgui_module: fake_imgui_module) -> None:
            received["imgui"] = imgui_module

        from arepy.ecs.systems import SystemPipeline

        world.add_system(SystemPipeline.RENDER_UI, ui_system)
        engine.set_current_world("main")
        engine._ArepyEngine__check_and_set_world()
        engine._ArepyEngine__render_process()

        assert engine.get_resource(fake_imgui_module) is fake_imgui_module
        assert world.get_resource(fake_imgui_module) is fake_imgui_module
        assert received == {"imgui": fake_imgui_module}

    def test_imgui_backend_preserves_renderer_texture_flag(self, monkeypatch):
        from arepy.engine.integrations.imgui import backend as backend_module

        original_backend_init = backend_module.ModernGLRenderer.__init__
        original_get_platform_io = backend_module.imgui.get_platform_io

        fake_platform_io = SimpleNamespace(
            platform_get_clipboard_text_fn=None,
            platform_set_clipboard_text_fn=None,
        )
        renderer_has_textures = (
            backend_module.imgui.BackendFlags_.renderer_has_textures.value
        )

        def fake_renderer_init(self, *args, **kwargs) -> None:
            self.io = SimpleNamespace(
                backend_flags=renderer_has_textures,
                mouse_pos=None,
            )

        monkeypatch.setattr(
            backend_module.ModernGLRenderer,
            "__init__",
            fake_renderer_init,
        )
        monkeypatch.setattr(
            backend_module.moderngl,
            "get_context",
            lambda: object(),
        )
        monkeypatch.setattr(
            backend_module.imgui,
            "get_platform_io",
            lambda: fake_platform_io,
        )

        backend = backend_module.ImguiBackend()

        monkeypatch.setattr(
            backend_module.ModernGLRenderer,
            "__init__",
            original_backend_init,
        )
        monkeypatch.setattr(
            backend_module.imgui,
            "get_platform_io",
            original_get_platform_io,
        )

        assert (
            backend.io.backend_flags
            & backend_module.imgui.BackendFlags_.renderer_has_textures.value
        )

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
