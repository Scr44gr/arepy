"""
Demo: Stencil mask example

This demonstrates using the stencil buffer to mask content.
A circular mask is created and a texture is drawn through it.
"""

from arepy import ArepyEngine, Renderer2D, SystemPipeline
from arepy.ecs.world import World
from arepy.engine.renderer import Color, Rect


# Colors
WHITE = Color(255, 255, 255, 255)
RED = Color(255, 0, 0, 255)
BLUE = Color(0, 0, 255, 255)
GREEN = Color(0, 255, 0, 255)
DARK_GRAY = Color(40, 40, 40, 255)


def render_system(renderer: Renderer2D) -> None:
    """System that demonstrates stencil masking."""

    # Initialize stencil on first frame (only runs once internally)
    if not renderer.is_stencil_available():
        renderer.init_stencil()

    # Center of screen
    cx, cy = 400, 300
    radius = 150

    renderer.start_frame()
    renderer.clear(DARK_GRAY)

    if renderer.is_stencil_available():
        # 1. Begin stencil mask - draw shapes to define mask
        renderer.begin_stencil_mask()
        renderer.draw_circle((cx, cy), radius, WHITE)  # Circle mask
        renderer.end_stencil_mask()

        # 2. Draw content that will be masked
        # Only the part inside the circle will be visible
        renderer.draw_rectangle(Rect(200, 150, 400, 300), RED)
        renderer.draw_rectangle(Rect(250, 200, 100, 200), BLUE)
        renderer.draw_rectangle(Rect(450, 200, 100, 200), GREEN)

        # 3. End stencil mode
        renderer.end_stencil_mode()

        # Draw some UI outside the mask (normal rendering)
        renderer.draw_text("Stencil Mask Demo", (10, 10), 20, WHITE)
        renderer.draw_text("Content is masked by a circle", (10, 40), 16, WHITE)

        # Draw circle outline to show mask boundary
        renderer.draw_circle_lines((cx, cy), radius, WHITE)
    else:
        renderer.draw_text("Stencil not available", (10, 10), 20, RED)

    renderer.end_frame()


def main():
    engine = ArepyEngine(
        title="Stencil Mask Demo",
        width=800,
        height=600,
        vsync=True,
    )

    # Create a world with the demo system
    world: World = engine.create_world("main")
    world.add_system(SystemPipeline.RENDER, render_system)

    engine.set_current_world("main")
    engine.run()


if __name__ == "__main__":
    main()
