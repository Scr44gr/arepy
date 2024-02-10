from logging import getLogger

from sdl2 import (
    SDL_GL_ACCELERATED_VISUAL,
    SDL_GL_CONTEXT_FLAGS,
    SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG,
    SDL_GL_CONTEXT_MAJOR_VERSION,
    SDL_GL_CONTEXT_MINOR_VERSION,
    SDL_GL_CONTEXT_PROFILE_CORE,
    SDL_GL_CONTEXT_PROFILE_MASK,
    SDL_GL_DEPTH_SIZE,
    SDL_GL_DOUBLEBUFFER,
    SDL_GL_MULTISAMPLEBUFFERS,
    SDL_GL_MULTISAMPLESAMPLES,
    SDL_GL_STENCIL_SIZE,
    SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK,
    SDL_HINT_RENDER_DRIVER,
    SDL_HINT_VIDEO_HIGHDPI_DISABLED,
    SDL_INIT_EVERYTHING,
    SDL_WINDOWPOS_CENTERED,
    SDL_GetError,
    SDL_GL_CreateContext,
    SDL_GL_MakeCurrent,
    SDL_GL_SetAttribute,
    SDL_GL_SetSwapInterval,
    SDL_Init,
    SDL_SetHint,
)
from sdl2.ext import Window


def initialize_sdl_opengl(
    window_name: str, window_size: tuple[int, int], flags: int
) -> tuple:
    logger = getLogger(__name__)

    if SDL_Init(SDL_INIT_EVERYTHING) < 0:
        logger.error(
            f"SDL could not initialize! SDL Error: {SDL_GetError().decode('utf-8')}"
        )
        exit(1)

    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
    SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)
    SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
    SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 8)
    # SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE)

    SDL_SetHint(
        SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1"
    )  # Enable right click on Mac
    SDL_SetHint(SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")  # Disable high DPI scaling
    window = Window(
        window_name,
        window_size,
        position=(SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED),
        flags=flags,
    )

    if window is None:
        logger.error(
            f"Window could not be created! SDL Error: {SDL_GetError().decode('utf-8')}"
        )
        exit(1)

    gl_context = SDL_GL_CreateContext(window.window)

    SDL_GL_MakeCurrent(window.window, gl_context)
    SDL_GL_SetSwapInterval(1)  # Enable vsync (1 for enabled, 0 for disabled)

    if gl_context is None:
        logger.error(
            f"Cannot create OpenGL Context! SDL Error: {SDL_GetError().decode('utf-8')}"
        )
        exit(1)

    return window, gl_context
