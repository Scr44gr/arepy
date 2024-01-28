from typing import Tuple

import sdl2
from glm import vec2
from sdl2.keyboard import SDL_Keycode

from arepy import Arepy

from .components import Animation, KeyboardControlled, Rigidbody, Sprite, Transform
from .systems import AnimationSystem, MovementSystem, PlayerMovementSystem, RenderSystem


class MyGame(Arepy):
    title: str = "My Game"
    screen_width: int = 640
    screen_height: int = 480
    screen_size: Tuple[int, int] = (340, 240)
    max_frame_rate: int = 60
    fullscreen: bool = False
    fake_fullscreen: bool = True
    debug: bool = True

    def setup(self):
        # init engine
        self.init()
        # add assets
        self.get_asset_store().load_texture(
            self.renderer, "chopper", "./assets/chopper-spritesheet.png"
        )
        self.get_asset_store().load_texture(
            self.renderer, "jungle", "./assets/tilesets/jungle.png"
        )
        self.get_asset_store().load_texture(
            self.renderer, "gege", "./assets/gege-idle.png"
        )

        # Add the tile
        tile_size = 32
        tile_scale = 1.0
        file_map = open("./assets/tilesets/jungle.map", "r")
        map_data = file_map.read()
        file_map.close()

        map_cols: int = 25
        map_rows: int = 20
        for y in range(map_rows):
            for x in range(map_cols):
                rect_y = map_data[y * map_cols * 3 + x * 3]
                rect_x = map_data[y * map_cols * 3 + x * 3 + 1]
                rect_y = int(rect_y)
                rect_x = int(rect_x)
                tile_entity = self.create_entity()
                tile_entity.with_component(
                    Transform(
                        position=vec2(
                            x * (tile_scale * tile_size),
                            y * (tile_scale * tile_size),
                        ),
                        rotation=0.0,
                        scale=vec2(tile_scale, tile_scale),
                    )
                )
                tile_entity.with_component(
                    Sprite(
                        width=tile_size,
                        height=tile_size,
                        asset_id="jungle",
                        src_rect=(rect_x * tile_size, rect_y * tile_size),
                        z_index=1,
                    )
                )
                tile_entity = tile_entity.build()

        # Player Creation
        entity_builder = self.create_entity()
        entity_builder.with_component(
            Transform(position=vec2(0, 0), rotation=0, scale=vec2(1, 1))
        )
        entity_builder.with_component(
            Rigidbody(velocity=vec2(0, 0), acceleration=vec2(0, 0))
        )
        entity_builder.with_component(
            Sprite(width=37, height=64, src_rect=(0, 0), z_index=2, asset_id="gege")
        )
        entity_builder.with_component(
            KeyboardControlled(
                up_velocity=vec2(0, -100),
                down_velocity=vec2(0, 100),
                left_velocity=vec2(-100, 0),
                right_velocity=vec2(100, 0),
            )
        )
        entity_builder.with_component(
            Animation(
                start_time=0,
                current_frame=1,
                frame_count=3,
                frame_speed_rate=8,
                is_playing=True,
                repeat=True,
            )
        )
        # A player is born
        player = entity_builder.build()

        # System Creation
        self.add_system(MovementSystem)
        self.add_system(RenderSystem)
        self.add_system(PlayerMovementSystem)
        self.add_system(AnimationSystem)

        # Initialized handlers

    def on_startup(self):
        ...

    def on_shutdown(self):
        ...

    def on_update(self):
        self.get_system(MovementSystem).update(delta_time=self.delta_time)
        self.get_system(PlayerMovementSystem).update(
            keyboard_handler=self.get_keyboard_event_handler(),
            delta_time=self.delta_time,
        )

    def on_render(self):
        self.get_system(RenderSystem).update(
            renderer=self.renderer,
            asset_store=self.get_asset_store(),
        )
        self.get_system(AnimationSystem).update(delta_time=self.delta_time)


if __name__ == "__main__":
    arepy = MyGame()
    arepy.setup()
    arepy.run()
