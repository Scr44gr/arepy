from arepy.asset_store import AssetStore
from arepy.bundle.components import Sprite, Transform
from arepy.ecs.query import Query, With
from arepy.ecs.registry import Entity
from arepy.engine.renderer.renderer_2d import Color, Rect, Renderer2D

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
    query: Query[Entity, With[Transform, Sprite]],
    renderer: Renderer2D,
    asset_store: AssetStore,
):
    renderer.start_frame()
    renderer.clear(color=Color(245, 245, 245, 255))
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
    renderer.draw_fps((10, 10))
    renderer.end_frame()
