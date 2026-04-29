from __future__ import annotations

from arepy import (
    ArepyEngine,
    Color,
    Display,
    Renderer2D,
    SystemPipeline,
    Time,
    World,
    imgui,
    WindowFlag,
)

WIDTH = 960
HEIGHT = 540
TEXT = Color(236, 240, 255, 255)
MUTED = Color(163, 174, 197, 255)
background_rgb: list[float] = [0.10, 0.13, 0.18]
show_demo_window = False
title_clicks = 0


def require_imgui() -> None:
    if imgui is None:
        raise RuntimeError(
            "Install the optional imgui extra first: uv sync --extra imgui"
        )


def background_color() -> Color:
    red, green, blue = background_rgb
    return Color(int(red * 255), int(green * 255), int(blue * 255), 255)


def render_scene(renderer: Renderer2D, time: Time) -> None:
    renderer.start_frame()
    renderer.clear(background_color())
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


def render_imgui(world: World, display: Display, time: Time) -> None:
    global background_rgb, show_demo_window, title_clicks

    world.get_resource(imgui)

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
        imgui.text("imgui is also registered as a global engine resource.")
        imgui.text("No wrapper class and no manual new_frame/render calls.")
        imgui.text(f"frame time: {time.delta_seconds * 1000.0:.2f} ms")

        _, background_rgb = imgui.color_edit3(
            "background",
            background_rgb,
        )
        _, show_demo_window = imgui.checkbox(
            "show Dear ImGui demo",
            show_demo_window,
        )

        if imgui.button("Change window title"):
            title_clicks += 1
            display.set_window_title(f"Arepy imgui example ({title_clicks})")
    imgui.end()

    if show_demo_window:
        show_demo_window = bool(imgui.show_demo_window(show_demo_window))


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

    @world.on_startup
    def verify_imgui_resource() -> None:
        assert world.get_resource(imgui) is imgui

    world.add_system(SystemPipeline.RENDER, render_scene)
    world.add_system(SystemPipeline.RENDER_UI, render_imgui)
    game.set_current_world("imgui_minimal")
    game.run()


if __name__ == "__main__":
    main()
