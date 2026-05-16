from arepy_ecs import Entity, Query, With

from arepy.asset_store import AssetStore
from arepy.bundle.components import Sprite, Transform
from arepy.engine.renderer.renderer_2d import Color, Rect, Renderer2D

WHITE = Color(255, 255, 255, 255)
CLEAR_COLOR = Color(245, 245, 245, 255)

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
    renderer.clear(color=CLEAR_COLOR)
    for transform, sprite in query.iter_components(Transform, Sprite):
        position = transform.position
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
            WHITE,
        )
    renderer.draw_fps((10, 10))
    renderer.end_frame()
