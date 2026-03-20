from types import SimpleNamespace

from arepy.engine.engine import ArepyEngine


class FakeDisplay:
    def __init__(self):
        self._should_close = False

    def set_vsync(self, enabled: bool) -> None:
        self.vsync = enabled

    def create_window(self, width: int, height: int, title: str) -> None:
        self.window = (width, height, title)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = True

    def set_window_icon(self, icon_path) -> None:
        self.icon_path = icon_path

    def window_should_close(self) -> bool:
        return self._should_close


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
        monkeypatch.setattr("arepy.container.dependencies", lambda: make_fake_dependencies())

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
        monkeypatch.setattr("arepy.container.dependencies", lambda: make_fake_dependencies())

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
        monkeypatch.setattr("arepy.container.dependencies", lambda: make_fake_dependencies())

        engine = ArepyEngine()
        world = engine.create_world("main")

        assert world.get_resource(ArepyEngine) is engine