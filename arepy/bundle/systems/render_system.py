from ...asset_store import AssetStore
from ...ecs import System
from ...engine.renderer.renderer_2d_repository import Color, Rect, Renderer2DRepository
from ..components import Sprite, Transform


class RenderSystem(System):
    def __init__(self):
        super().__init__()
        self.require_components([Transform, Sprite])

    def update(
        self,
        renderer: Renderer2DRepository,
        asset_store: AssetStore,
    ):

        for entity in self.get_entities():
            position = entity.get_component(Transform).position
            sprite = entity.get_component(Sprite)
            texture = asset_store.get_texture(sprite.asset_id)
            texture_size = texture.get_size()
            dst_rect = Rect(
                position.x,
                position.y,
                int(texture_size[0]),
                int(texture_size[1]),
            )
            src_rect = Rect(
                float(sprite.src_rect[0]),
                float(sprite.src_rect[1]),
                int(sprite.src_rect[2]),
                int(sprite.src_rect[3]),
            )

            renderer.draw_texture(
                texture,
                src_rect,
                dst_rect,
                Color(255, 255, 255, 255),
            )
