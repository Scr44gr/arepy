from ...asset_store import AssetStore
from ...ecs import System
from ...engine.renderer import BaseRenderer
from ..components import Sprite, Transform


class RenderSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Transform, Sprite])

    def update(
        self,
        dt: float,
        renderer: BaseRenderer,
        asset_store: AssetStore,
    ):

        for entity in self.get_entities():
            position = entity.get_component(Transform).position
            sprite = entity.get_component(Sprite)
            texture = asset_store.get_texture(sprite.asset_id)
            texture_size = texture.get_size()
            dst_rect = (
                float(texture_size[0]),
                float(texture_size[1]),
                position.x,
                position.y,
            )
            src_rect = (
                float(sprite.src_rect[0]),
                float(sprite.src_rect[1]),
                float(sprite.src_rect[2]),
                float(sprite.src_rect[3]),
            )

            renderer.draw_sprite(
                texture,
                src_rect,
                dst_rect,
                (255, 255, 255, 255),
            )
