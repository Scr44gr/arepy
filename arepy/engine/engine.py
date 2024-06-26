from typing import Type

import OpenGL.GL as gl
import sdl2
from sdl2 import SDL_DestroyWindow, SDL_GL_DeleteContext, SDL_GL_SwapWindow
from sdl2.ext import get_events

from ..arepy_imgui import ImguiRenderer, imgui
from ..asset_store import AssetStore
from ..builders import EntityBuilder
from ..ecs.registry import Registry
from ..ecs.systems import TSystem
from ..event_manager import EventManager

# Default events
from ..event_manager.events.keyboard_event import (
    KeyboardPressedEvent,
    KeyboardReleasedEvent,
)
from ..event_manager.events.sdl_event import SDLEvent
from ..event_manager.handlers.keyboard_event_handler import KeyboardEventHandler
from .display import initialize_sdl_opengl
from .renderer.opengl.opengl import OpenGLRenderer


class Engine:
    title: str = "Arepy Engine"
    window_width: int = 640
    window_height: int = 480
    # Logical size
    screen_size = (window_width, window_height)
    max_frame_rate: int = 60
    debug: bool = False
    fullscreen: bool = False
    fake_fullscreen: bool = False

    def __init__(self): ...

    def _initialize_engine(self):
        self._is_running = False
        self._ms_prev_frame = 0
        self._ms_per_frame = 1000 / self.max_frame_rate
        self._registry = Registry()
        self._asset_store = AssetStore()
        self._event_manager = EventManager()
        self._keyboard_event_handler = KeyboardEventHandler(self._event_manager)

    def init(self):
        self._initialize_engine()
        full_screen_flag = sdl2.SDL_WINDOW_FULLSCREEN if self.fullscreen else 0
        fake_full_screen_flag = (
            sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP if self.fake_fullscreen else 0
        )
        flags = (
            sdl2.SDL_WINDOW_SHOWN
            | full_screen_flag
            | fake_full_screen_flag
            | sdl2.SDL_WINDOW_OPENGL
            | sdl2.SDL_WINDOW_RESIZABLE
        )
        self.window, self.gl_context = initialize_sdl_opengl(
            self.title,
            window_size=(self.window_width, self.window_height),
            flags=flags,
        )
        imgui.create_context()
        self.impl = ImguiRenderer(self.window.window)  # type: ignore
        self.renderer = OpenGLRenderer(
            self.screen_size, (self.window_width, self.window_height)
        )

    def run(self):

        self._is_running = True
        self.on_startup()
        while self._is_running:
            self.__input_process()
            self.__update_process()
            self.__render_process()

        self.on_shutdown()

    def __input_process(self):
        for event in get_events():
            if event.type == sdl2.SDL_QUIT:
                self._is_running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    self._is_running = False
                key_pressed_event = KeyboardPressedEvent((event.key.keysym.sym))
                self._event_manager.emit(key_pressed_event)
            elif event.type == sdl2.SDL_KEYUP:
                key_released_event = KeyboardReleasedEvent((event.key.keysym.sym))
                self._event_manager.emit(key_released_event)
            # on resize
            elif event.type == sdl2.SDL_WINDOWEVENT:
                if (
                    event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED
                    or event.window.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED
                    or event.window.event == sdl2.SDL_WINDOWEVENT_MAXIMIZED
                    or event.window.event == sdl2.SDL_WINDOWEVENT_RESTORED
                    or event.window.event == sdl2.SDL_WINDOWEVENT_MINIMIZED
                    or event.window.event == sdl2.SDL_WINDOWEVENT_EXPOSED
                    or event.window.event == sdl2.SDL_WINDOWEVENT_ENTER
                ):
                    self.window_width = event.window.data1
                    self.window_height = event.window.data2
                    if self.window_width < 1 or self.window_height < 1:
                        return
                    self.screen_size = (self.window_width, self.window_height)
                    self.renderer.set_window_size(self.screen_size)
            self._event_manager.emit(SDLEvent(event))
            self.impl.process_event(event)
        self.impl.process_inputs()

    def __update_process(self):
        time_to_wait = self._ms_per_frame - (sdl2.SDL_GetTicks() - self._ms_prev_frame)
        if time_to_wait > 0 and time_to_wait <= self._ms_per_frame:
            sdl2.SDL_Delay(int(time_to_wait))

        self.delta_time = (sdl2.SDL_GetTicks() - self._ms_prev_frame) / 1000.0
        self._ms_prev_frame = sdl2.SDL_GetTicks()
        self.on_update()
        self._registry.update()

    def __render_process(self):

        self.renderer.clear()
        imgui.new_frame()
        self.renderer.start_frame()
        self.on_render()
        imgui.end_frame()  # type: ignore
        imgui.render()
        self.renderer.end_frame()
        self.renderer.flush()
        self.impl.render(imgui.get_draw_data())  # type: ignore
        SDL_GL_SwapWindow(self.window.window)

    def __del__(self):
        SDL_GL_DeleteContext(self.gl_context)
        SDL_DestroyWindow(self.window.window)
        sdl2.SDL_Quit()

    def create_entity(self) -> EntityBuilder:
        """Create an entity builder.

        Returns:
            An entity builder.
        """
        entity = self._registry.create_entity()
        return EntityBuilder(entity, self._registry)

    def add_system(self, system: Type[TSystem]) -> None:
        """Create a new system.

        Args:
            system: A system.
        """
        self._registry.add_system(system)

    def get_system(self, system_type: Type[TSystem]) -> TSystem:
        """Get a system.

        Args:
            system_type: The system type.

        Returns:
            The system.
        """
        system = self._registry.get_system(system_type)
        if not system:
            raise RuntimeError(f"System {system_type} does not exist.")
        return system

    def get_asset_store(self) -> AssetStore:
        """Get the asset store.

        Returns:
            The asset store.
        """
        return self._asset_store

    def get_event_manager(self) -> EventManager:
        """Get the event manager.

        Returns:
            The event manager.
        """
        return self._event_manager

    def get_keyboard_event_handler(self) -> KeyboardEventHandler:
        """Get the keyboard event handler.

        Returns:
            The keyboard event handler.
        """
        return self._keyboard_event_handler

    # Engine func Events
    def on_startup(self): ...
    def on_update(self): ...
    def on_shutdown(self): ...
    def on_render(self): ...
