from typing import cast

import numpy as np

from arepy.asset_store import AssetStore
from arepy.bundle.components import Sprite, Transform
from arepy.ecs.query import BatchQuery
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
    batch: BatchQuery[Transform, Sprite],
    renderer: Renderer2D,
    asset_store: AssetStore,
):
    renderer.start_frame()
    renderer.clear(color=CLEAR_COLOR)
    texture_atlas = asset_store.get_texture_atlas()
    if texture_atlas is not None and texture_atlas.atlases:
        position = batch.vec2(Transform, "position")
        origin = batch.vec2(Transform, "origin")
        rotation = batch.scalar(
            Transform,
            "rotation",
            dtype=np.float64,
            writeback=False,
            bind=True,
        )
        sprites = cast(list[Sprite], batch.components(Sprite))
        batch_layout = texture_atlas.get_batch_layout(sprites)
        renderer.draw_texture_batch(
            texture_atlas,
            batch_layout,
            position.x,
            position.y,
            batch_layout.default_dest_width,
            batch_layout.default_dest_height,
            origin.x,
            origin.y,
            rotation,
            WHITE,
        )
    else:
        for transform, sprite in batch.iter_components(Transform, Sprite):
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
            renderer.draw_texture_ex(
                texture,
                src_rect,
                dst_rect,
                (transform.origin.x, transform.origin.y),
                transform.rotation,
                WHITE,
            )
    renderer.draw_fps((10, 10))
    renderer.end_frame()
