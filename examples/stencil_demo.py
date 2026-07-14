"""
Demo: Stencil mask example

This demonstrates using the stencil buffer to mask content.
A circular mask is created and a texture is drawn through it.
"""

from dataclasses import dataclass

from arepy import ArepyEngine, Renderer2D, SystemPipeline, WindowFlag
from arepy.ecs.world import World
from arepy.engine.renderer import Color, Rect


# Colors
WHITE = Color(255, 255, 255, 255)
RED = Color(255, 0, 0, 255)
BLUE = Color(0, 0, 255, 255)
GREEN = Color(0, 255, 0, 255)
DARK_GRAY = Color(40, 40, 40, 255)
CENTER = (400, 300)
MASK_CONTENT = Rect(200, 150, 400, 300)
BLUE_BAR = Rect(250, 200, 100, 200)
GREEN_BAR = Rect(450, 200, 100, 200)


@dataclass(slots=True)
class StencilState:
    available: bool = False


def render_system(renderer: Renderer2D, stencil: StencilState) -> None:
    """System that demonstrates stencil masking."""
    radius = 150

    renderer.start_frame()
    renderer.clear(DARK_GRAY)

    if stencil.available:
        # 1. Begin stencil mask - draw shapes to define mask
        renderer.begin_stencil_mask()
        renderer.draw_circle(CENTER, radius, WHITE)  # Circle mask
        renderer.end_stencil_mask()

        # 2. Draw content that will be masked
        # Only the part inside the circle will be visible
        renderer.draw_rectangle(MASK_CONTENT, RED)
        renderer.draw_rectangle(BLUE_BAR, BLUE)
        renderer.draw_rectangle(GREEN_BAR, GREEN)

        # 3. End stencil mode
        renderer.end_stencil_mode()

        # Draw some UI outside the mask (normal rendering)
        renderer.draw_text("Stencil Mask Demo", (10, 10), 20, WHITE)
        renderer.draw_text("Content is masked by a circle", (10, 40), 16, WHITE)

        # Draw circle outline to show mask boundary
        renderer.draw_circle_lines(CENTER, radius, WHITE)
    else:
        renderer.draw_text("Stencil not available", (10, 10), 20, RED)

    renderer.end_frame()


def main() -> None:
    engine = ArepyEngine(
        title="Stencil Mask Demo",
        width=800,
        height=600,
        window_flags=WindowFlag.VSYNC_HINT,
    )

    stencil = StencilState()
    engine.add_resource(stencil)
    # Create a world with the demo system.
    world: World = engine.create_world("main")

    @world.on_startup
    def initialize_stencil() -> None:
        # The graphics context exists here, so initialization is attempted once.
        stencil.available = engine.renderer_2d.init_stencil()

    world.add_system(SystemPipeline.RENDER, render_system)

    engine.set_current_world("main")
    engine.run()


if __name__ == "__main__":
    main()
