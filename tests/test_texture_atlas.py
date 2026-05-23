import pytest

from arepy.bundle.components import Sprite
from arepy.engine.renderer import ArepyTexture
from arepy.engine.renderer.texture_atlas import (
    TextureAtlas,
    TextureAtlasCollection,
    TextureAtlasRegion,
    _pack_texture_pages,
)


def _make_texture(texture_id: int, size: tuple[int, int]) -> ArepyTexture:
    return ArepyTexture(texture_id, size)


def test_pack_texture_pages_spills_when_page_is_full() -> None:
    texture_items = [
        ("hero", _make_texture(1, (32, 32))),
        ("enemy", _make_texture(2, (40, 16))),
        ("coin", _make_texture(3, (40, 20))),
    ]

    pages = _pack_texture_pages(texture_items, max_size=(64, 64), padding=0)

    assert len(pages) == 2
    assert tuple(placement.asset_id for placement in pages[0].placements) == (
        "hero",
        "enemy",
    )
    assert tuple(placement.asset_id for placement in pages[1].placements) == ("coin",)


def test_texture_batch_plan_groups_sprites_by_atlas_and_reuses_cache() -> None:
    atlas_0 = TextureAtlas(texture=_make_texture(10, (64, 64)), index=0, size=(64, 64))
    atlas_1 = TextureAtlas(texture=_make_texture(11, (64, 64)), index=1, size=(64, 64))
    atlas_collection = TextureAtlasCollection(
        atlases=(atlas_0, atlas_1),
        regions={
            "hero": TextureAtlasRegion(atlas_index=0, x=0, y=0, width=32, height=32),
            "enemy": TextureAtlasRegion(atlas_index=1, x=8, y=4, width=16, height=16),
        },
    )
    sprites = [
        Sprite("hero", (0, 0, 16, 16), 0),
        Sprite("enemy", (0, 0, 16, 16), 0),
        Sprite("hero", (8, 8, 8, 8), 0),
    ]

    first_plan = atlas_collection.get_batch_plan(sprites)
    second_plan = atlas_collection.get_batch_plan(sprites)

    assert first_plan is second_plan
    assert len(first_plan.groups) == 2

    hero_group = first_plan.groups[0]
    enemy_group = first_plan.groups[1]

    assert hero_group.texture is atlas_0.texture
    assert hero_group.entity_indices.tolist() == [0, 2]
    assert hero_group.source_x.tolist() == [0.0, 8.0]
    assert hero_group.source_y.tolist() == [0.0, 8.0]
    assert hero_group.source_width.tolist() == [16.0, 8.0]
    assert hero_group.source_height.tolist() == [16.0, 8.0]

    assert enemy_group.texture is atlas_1.texture
    assert enemy_group.entity_indices.tolist() == [1]
    assert enemy_group.source_x.tolist() == [8.0]
    assert enemy_group.source_y.tolist() == [4.0]


def test_texture_batch_plan_refreshes_when_sprite_frame_changes() -> None:
    atlas = TextureAtlas(texture=_make_texture(10, (64, 64)), index=0, size=(64, 64))
    atlas_collection = TextureAtlasCollection(
        atlases=(atlas,),
        regions={
            "hero": TextureAtlasRegion(atlas_index=0, x=4, y=6, width=32, height=32),
        },
    )
    sprites = [Sprite("hero", (0, 0, 16, 16), 0)]

    first_plan = atlas_collection.get_batch_plan(sprites)
    sprites[0].src_rect = (8, 12, 8, 8)
    second_plan = atlas_collection.get_batch_plan(sprites)

    assert second_plan is not first_plan
    assert second_plan.groups[0].source_x.tolist() == [12.0]
    assert second_plan.groups[0].source_y.tolist() == [18.0]
    assert second_plan.groups[0].source_width.tolist() == [8.0]
    assert second_plan.groups[0].source_height.tolist() == [8.0]


def test_texture_batch_plan_requires_at_least_one_atlas() -> None:
    atlas_collection = TextureAtlasCollection(atlases=(), regions={})

    with pytest.raises(RuntimeError, match="at least one texture atlas"):
        atlas_collection.get_batch_plan([Sprite("hero", (0, 0, 16, 16), 0)])