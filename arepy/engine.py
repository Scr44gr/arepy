import sdl2
from sdl2.ext import Renderer, Resources, Window, get_events

from .builders import EntityBuilder
from .ecs.registry import Registry


class Engine:
    title: str = "Arepy Engine"
    screen_width: int = 640
    screen_height: int = 480
    max_frame_rate: int = 60
    debug: bool = True

    def __init__(self):
        self._is_running = False
        self._ms_prev_frame = 0
        self._ms_per_frame = 1000 / self.max_frame_rate
        self._registry = Registry()

    def init(self):
        sdl2.SDL_Init(sdl2.SDL_INIT_EVERYTHING)
        self.window = Window(
            self.title,
            size=(self.screen_width, self.screen_height),
            flags=sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_OPENGL,
        )
        self.renderer = Renderer(self.window)

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

    def __render_process(self):
        self.renderer.clear()
        if self.debug:
            self.window.title = f"[DEBUG] {self.title} - FPS: {1 / self.delta_time:.2f}"

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

    def on_startup(self):
        # create imgui window
        pass

    def on_update(self):
        pass

    def on_shutdown(self):
        pass


if __name__ == "__main__":
    engine = Engine()
    engine.init()
    engine.run()
