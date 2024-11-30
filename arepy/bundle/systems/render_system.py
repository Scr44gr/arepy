from random import choice

from arepy.ecs.query import EntityWith, Query

from ...asset_store import AssetStore
from ...engine.renderer.renderer_2d import Color, Rect, Renderer2D
from ..components import Sprite, Transform

COLORS = [
    Color(255, 0, 0, 255),  # red
    Color(0, 255, 0, 255),  # green
    Color(0, 0, 255, 255),  # blue
    Color(255, 255, 0, 255),  # yellow
    Color(0, 255, 255, 255),  # cyan
    Color(255, 0, 255, 255),  # magenta
    Color(255, 255, 255, 255),  # white
    Color(0, 0, 0, 255),  # black
]


def render_system(
    query: Query[EntityWith[Transform, Sprite]],
    renderer: Renderer2D,
    asset_store: AssetStore,
):
    for entity in query.get_entities():
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
