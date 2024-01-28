from typing import Type

import sdl2
from sdl2.ext import Renderer, Resources, Window, get_events
from sdl2.sdlttf import TTF_Init, TTF_Quit

from .asset_store import AssetStore
from .builders import EntityBuilder
from .ecs.registry import Registry
from .ecs.systems import System, TSystem
from .event_manager import EventManager

# Default events
from .event_manager.events.keyboard_event import (
    KeyboardPressedEvent,
    KeyboardReleasedEvent,
)
from .event_manager.handlers.keyboard_event_handler import KeyboardEventHandler


class Engine:
    title: str = "Arepy Engine"
    screen_width: int = 640
    screen_height: int = 480
    # Logical size
    screen_size = (screen_width, screen_height)
    max_frame_rate: int = 60
    debug: bool = False
    fullscreen: bool = False
    fake_fullscreen: bool = False

    def __init__(self):
        self._is_running = False
        self._ms_prev_frame = 0
        self._ms_per_frame = 1000 / self.max_frame_rate
        self._registry = Registry()
        self._asset_store = AssetStore()
        self._event_manager = EventManager()
        self._keyboard_event_handler = KeyboardEventHandler(self._event_manager)

    def init(self):
        sdl2.SDL_Init(sdl2.SDL_INIT_EVERYTHING)
        TTF_Init()
        full_screen_flag = sdl2.SDL_WINDOW_FULLSCREEN if self.fullscreen else 0
        fake_full_screen_flag = (
            sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP if self.fake_fullscreen else 0
        )
        self.window = Window(
            self.title,
            size=self.screen_size,
            flags=sdl2.SDL_WINDOW_SHOWN | (full_screen_flag | fake_full_screen_flag),
        )
        self.renderer = Renderer(
            self.window,
            flags=sdl2.SDL_RENDERER_ACCELERATED
            | sdl2.SDL_RENDERER_PRESENTVSYNC
            | sdl2.SDL_RENDERER_TARGETTEXTURE,
            logical_size=(self.screen_width, self.screen_height),
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
        if self.debug:
            current_fps = 1 // self.delta_time
            self.window.title = f"[DEBUG] {self.title} - FPS: {current_fps:.2f}"
        self.on_render()
        self.renderer.present()

    def __del__(self):
        sdl2.SDL_Quit()
        TTF_Quit()

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

    def on_startup(self):
        pass

    def on_update(self):
        pass

    def on_shutdown(self):
        pass

    def on_render(self):
        pass


if __name__ == "__main__":
    engine = Engine()
    engine.init()
    engine.run()
