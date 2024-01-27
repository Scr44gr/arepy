from typing import Type

import sdl2
from sdl2.ext import Renderer, Resources, Window, get_events

from .asset_store import AssetStore
from .builders import EntityBuilder
from .ecs.registry import Registry
from .ecs.systems import System, TSystem


class Engine:
    title: str = "Arepy Engine"
    screen_width: int = 640
    screen_height: int = 480
    max_frame_rate: int = 60
    debug: bool = True
    fullscreen: bool = False

    def __init__(self):
        self._is_running = False
        self._ms_prev_frame = 0
        self._ms_per_frame = 1000 / self.max_frame_rate
        self._registry = Registry()
        self._asset_store = AssetStore()

    def init(self):
        sdl2.SDL_Init(sdl2.SDL_INIT_EVERYTHING)
        full_screen_flag = sdl2.SDL_WINDOW_FULLSCREEN if self.fullscreen else 0
        self.window = Window(
            self.title,
            size=(self.screen_width, self.screen_height),
            flags=sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_OPENGL | full_screen_flag,
        )
        self.renderer = Renderer(
            self.window,
            flags=sdl2.SDL_RENDERER_ACCELERATED
            | sdl2.SDL_RENDERER_PRESENTVSYNC
            | sdl2.SDL_RENDERER_TARGETTEXTURE,
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
            self.window.title = f"[DEBUG] {self.title} - FPS: {1 / self.delta_time:.2f}"
        self.on_render()
        self.renderer.present()

    def __del__(self):
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
