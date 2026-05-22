from ...ecs import Component
from ._field_views import InternedStringTable

_ASSET_IDS = InternedStringTable()


class Sprite(Component):
    asset_id_handle: int = 0
    src_x: int = 0
    src_y: int = 0
    src_w: int = 0
    src_h: int = 0
    z_index: int = 0
    flipped: bool = False


def make_sprite(
    asset_id: str,
    src_rect: tuple[int, int, int, int],
    z_index: int,
    flipped: bool = False,
) -> Sprite:
    return Sprite(
        asset_id_handle=_ASSET_IDS.intern(asset_id),
        src_x=src_rect[0],
        src_y=src_rect[1],
        src_w=src_rect[2],
        src_h=src_rect[3],
        z_index=z_index,
        flipped=flipped,
    )


def resolve_sprite_asset_id(sprite: Sprite) -> str:
    asset_id = _ASSET_IDS.resolve(sprite.asset_id_handle)
    if not isinstance(asset_id, str):
        raise ValueError("Sprite asset_id_handle is not initialized")
    return asset_id
