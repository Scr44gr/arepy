from __future__ import annotations

from dataclasses import dataclass, field

from arepy import (
    ArepyEngine,
    Color,
    Display,
    Input,
    Key,
    MouseButton,
    Renderer2D,
    SystemPipeline,
    Time,
    imgui,
    WindowFlag,
)

WIDTH = 960
HEIGHT = 540
TEXT = Color(236, 240, 255, 255)
MUTED = Color(163, 174, 197, 255)
BACKGROUND = Color(26, 33, 46, 255)


@dataclass(slots=True)
class ImguiDemoState:
    background_rgb: list[float] = field(
        default_factory=lambda: [0.10, 0.13, 0.18]
    )
    show_demo_window: bool = False
    title_clicks: int = 0


def require_imgui() -> None:
    if imgui is None:
        raise RuntimeError(
            "Install the optional imgui extra first: uv sync --extra imgui"
        )


def update_background_color(state: ImguiDemoState) -> None:
    red, green, blue = state.background_rgb
    BACKGROUND.r = int(red * 255)
    BACKGROUND.g = int(green * 255)
    BACKGROUND.b = int(blue * 255)


def render_scene(
    renderer: Renderer2D,
    time: Time,
    state: ImguiDemoState,
) -> None:
    update_background_color(state)
    renderer.start_frame()
    renderer.clear(BACKGROUND)
    renderer.draw_text("Arepy + imgui", (20, 18), 30, TEXT)
    renderer.draw_text(
        "The imgui window is rendered by the RENDER_UI pipeline.",
        (20, 56),
        18,
        MUTED,
    )
    renderer.draw_text(
        f"elapsed time: {time.elapsed_seconds:.2f}s",
        (20, 82),
        18,
        MUTED,
    )
    renderer.draw_fps((20, HEIGHT - 28))
    renderer.end_frame()


def handle_scene_input(input_device: Input, state: ImguiDemoState) -> None:
    """Keep game input separate from interactions captured by imgui."""

    io = imgui.get_io()
    if not io.want_capture_keyboard and input_device.is_key_pressed(Key.SPACE):
        state.background_rgb[0] = 0.10
        state.background_rgb[1] = 0.13
        state.background_rgb[2] = 0.18

    if not io.want_capture_mouse and input_device.is_mouse_button_pressed(
        MouseButton.RIGHT
    ):
        state.background_rgb[0] = 0.18
        state.background_rgb[1] = 0.10
        state.background_rgb[2] = 0.16


def render_imgui(
    display: Display,
    time: Time,
    state: ImguiDemoState,
) -> None:
    imgui.set_next_window_pos(
        (18.0, 110.0),
        cond=imgui.Cond_.first_use_ever,
    )
    imgui.set_next_window_size(
        (340.0, 0.0),
        cond=imgui.Cond_.first_use_ever,
    )

    expanded, _ = imgui.begin(
        "Direct imgui",
        flags=imgui.WindowFlags_.always_auto_resize,
    )
    if expanded:
        imgui.text("Using imgui directly from arepy.")
        imgui.text("No wrapper class and no manual new_frame/render calls.")
        imgui.text(f"frame time: {time.delta_seconds * 1000.0:.2f} ms")

        io = imgui.get_io()
        imgui.separator()
        imgui.text(f"keyboard captured: {io.want_capture_keyboard}")
        imgui.text(f"mouse captured: {io.want_capture_mouse}")
        imgui.text_disabled("Space resets the scene; right click changes it.")

        _, state.background_rgb = imgui.color_edit3(
            "background",
            state.background_rgb,
        )
        _, state.show_demo_window = imgui.checkbox(
            "show Dear ImGui demo",
            state.show_demo_window,
        )

        if imgui.button("Change window title"):
            state.title_clicks += 1
            display.set_window_title(
                f"Arepy imgui example ({state.title_clicks})"
            )
    imgui.end()

    if state.show_demo_window:
        state.show_demo_window = bool(
            imgui.show_demo_window(state.show_demo_window)
        )


def main() -> None:
    require_imgui()

    game = ArepyEngine(
        title="Arepy imgui example",
        width=WIDTH,
        height=HEIGHT,
        max_frame_rate=0,
        window_flags=WindowFlag.WINDOW_RESIZABLE,
    )
    world = game.create_world("imgui_minimal")
    world.add_resource(ImguiDemoState())

    world.add_system(SystemPipeline.INPUT, handle_scene_input)
    world.add_system(SystemPipeline.RENDER, render_scene)
    world.add_system(SystemPipeline.RENDER_UI, render_imgui)
    game.set_current_world("imgui_minimal")
    game.run()


if __name__ == "__main__":
    main()
