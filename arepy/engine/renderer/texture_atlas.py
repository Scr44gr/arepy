from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

import numpy as np
from numpy.typing import NDArray
from raylib import ffi, rl

from ...bundle.components import Sprite
from . import ArepyTexture, TextureFilter

if TYPE_CHECKING:
    from ...asset_store import AssetStore
    from .renderer_2d import Renderer2D

Float32Array = NDArray[np.float32]
Int64Array = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class TextureAtlasRegion:
    atlas_index: int
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class TextureAtlas:
    texture: ArepyTexture
    index: int
    size: tuple[int, int]


@dataclass(frozen=True, slots=True)
class TextureBatchGroup:
    texture: ArepyTexture
    entity_indices: Int64Array
    source_x: Float32Array
    source_y: Float32Array
    source_width: Float32Array
    source_height: Float32Array


@dataclass(frozen=True, slots=True)
class TextureBatchPlan:
    groups: tuple[TextureBatchGroup, ...]


@dataclass(frozen=True, slots=True)
class _AtlasPlacement:
    asset_id: str
    texture: ArepyTexture
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class _AtlasPageLayout:
    size: tuple[int, int]
    placements: tuple[_AtlasPlacement, ...]


@dataclass(slots=True)
class _PlanCacheEntry:
    signature: tuple[tuple[str, tuple[int, int, int, int]], ...]
    plan: TextureBatchPlan


@dataclass(slots=True)
class TextureAtlasCollection:
    atlases: tuple[TextureAtlas, ...]
    regions: dict[str, TextureAtlasRegion]
    _plan_cache: dict[tuple[int, int], _PlanCacheEntry] = field(default_factory=dict)

    def get_batch_plan(self, sprites: Sequence[Sprite]) -> TextureBatchPlan:
        if not self.atlases:
            raise RuntimeError("draw_texture_batch requires at least one texture atlas.")

        signature = tuple(
            (sprite.asset_id, tuple(int(value) for value in sprite.src_rect))
            for sprite in sprites
        )
        cache_key = (id(sprites), len(sprites))
        cached = self._plan_cache.get(cache_key)
        if cached is not None and cached.signature == signature:
            return cached.plan

        grouped_entity_indices: dict[int, list[int]] = {}
        grouped_source_x: dict[int, list[float]] = {}
        grouped_source_y: dict[int, list[float]] = {}
        grouped_source_width: dict[int, list[float]] = {}
        grouped_source_height: dict[int, list[float]] = {}

        for entity_index, sprite in enumerate(sprites):
            region = self.regions.get(sprite.asset_id)
            if region is None:
                raise KeyError(f"Texture atlas does not contain asset '{sprite.asset_id}'.")

            src_x = int(sprite.src_rect[0])
            src_y = int(sprite.src_rect[1])
            src_width = int(sprite.src_rect[2])
            src_height = int(sprite.src_rect[3])
            _validate_source_rect(sprite.asset_id, region, src_x, src_y, src_width, src_height)

            grouped_entity_indices.setdefault(region.atlas_index, []).append(entity_index)
            grouped_source_x.setdefault(region.atlas_index, []).append(float(region.x + src_x))
            grouped_source_y.setdefault(region.atlas_index, []).append(float(region.y + src_y))
            grouped_source_width.setdefault(region.atlas_index, []).append(float(src_width))
            grouped_source_height.setdefault(region.atlas_index, []).append(float(src_height))

        groups: list[TextureBatchGroup] = []
        for atlas in self.atlases:
            atlas_indices = grouped_entity_indices.get(atlas.index)
            if not atlas_indices:
                continue

            groups.append(
                TextureBatchGroup(
                    texture=atlas.texture,
                    entity_indices=np.asarray(atlas_indices, dtype=np.int64),
                    source_x=np.asarray(grouped_source_x[atlas.index], dtype=np.float32),
                    source_y=np.asarray(grouped_source_y[atlas.index], dtype=np.float32),
                    source_width=np.asarray(
                        grouped_source_width[atlas.index], dtype=np.float32
                    ),
                    source_height=np.asarray(
                        grouped_source_height[atlas.index], dtype=np.float32
                    ),
                )
            )

        plan = TextureBatchPlan(tuple(groups))
        self._plan_cache[cache_key] = _PlanCacheEntry(signature=signature, plan=plan)
        return plan

    def clear_plan_cache(self) -> None:
        self._plan_cache.clear()

    def unload(self, renderer: "Renderer2D") -> None:
        for atlas in self.atlases:
            renderer.unload_texture(atlas.texture)
        self.clear_plan_cache()


def build_texture_atlas(
    asset_store: "AssetStore",
    renderer: "Renderer2D",
    *,
    max_size: tuple[int, int] = (2048, 2048),
    padding: int = 1,
) -> TextureAtlasCollection:
    texture_items = list(asset_store.textures.items())
    if not texture_items:
        return TextureAtlasCollection((), {})

    page_layouts = _pack_texture_pages(texture_items, max_size=max_size, padding=padding)
    atlases: list[TextureAtlas] = []
    regions: dict[str, TextureAtlasRegion] = {}

    for atlas_index, page_layout in enumerate(page_layouts):
        atlas_texture = _build_atlas_texture(page_layout, renderer)
        atlases.append(
            TextureAtlas(
                texture=atlas_texture,
                index=atlas_index,
                size=page_layout.size,
            )
        )
        for placement in page_layout.placements:
            regions[placement.asset_id] = TextureAtlasRegion(
                atlas_index=atlas_index,
                x=placement.x,
                y=placement.y,
                width=placement.width,
                height=placement.height,
            )

    return TextureAtlasCollection(tuple(atlases), regions)


def _pack_texture_pages(
    texture_items: Sequence[tuple[str, ArepyTexture]],
    *,
    max_size: tuple[int, int],
    padding: int,
) -> tuple[_AtlasPageLayout, ...]:
    if max_size[0] <= 0 or max_size[1] <= 0:
        raise ValueError("Texture atlas max_size must be positive.")
    if padding < 0:
        raise ValueError("Texture atlas padding cannot be negative.")

    max_width, max_height = max_size
    page_layouts: list[_AtlasPageLayout] = []
    placements: list[_AtlasPlacement] = []
    cursor_x = 0
    cursor_y = 0
    row_height = 0
    used_width = 0
    used_height = 0

    def flush_page() -> None:
        nonlocal placements, cursor_x, cursor_y, row_height, used_width, used_height
        if not placements:
            return
        page_layouts.append(
            _AtlasPageLayout(
                size=(max(used_width, 1), max(used_height, 1)),
                placements=tuple(placements),
            )
        )
        placements = []
        cursor_x = 0
        cursor_y = 0
        row_height = 0
        used_width = 0
        used_height = 0

    for asset_id, texture in texture_items:
        width, height = texture.get_size()
        if width <= 0 or height <= 0:
            raise ValueError(f"Texture '{asset_id}' has an invalid size: {(width, height)}")
        if width > max_width or height > max_height:
            raise ValueError(
                f"Texture '{asset_id}' size {(width, height)} exceeds atlas max_size {max_size}."
            )

        if cursor_x > 0 and cursor_x + width > max_width:
            cursor_x = 0
            cursor_y += row_height + padding
            row_height = 0

        if cursor_y > 0 and cursor_y + height > max_height:
            flush_page()

        if cursor_x > 0 and cursor_x + width > max_width:
            cursor_x = 0
            cursor_y += row_height + padding
            row_height = 0

        if cursor_y > 0 and cursor_y + height > max_height:
            raise ValueError(
                f"Texture '{asset_id}' could not be packed into atlas size {max_size}."
            )

        placements.append(
            _AtlasPlacement(
                asset_id=asset_id,
                texture=texture,
                x=cursor_x,
                y=cursor_y,
                width=width,
                height=height,
            )
        )
        used_width = max(used_width, cursor_x + width)
        used_height = max(used_height, cursor_y + height)
        cursor_x += width + padding
        row_height = max(row_height, height)

    flush_page()
    return tuple(page_layouts)


def _build_atlas_texture(
    page_layout: _AtlasPageLayout,
    renderer: "Renderer2D",
) -> ArepyTexture:
    atlas_image = ffi.new(
        "Image *",
        rl.GenImageColor(page_layout.size[0], page_layout.size[1], (0, 0, 0, 0)),
    )
    try:
        for placement in page_layout.placements:
            texture_ref = _require_texture_ref(placement.texture)
            source_image = rl.LoadImageFromTexture(texture_ref)
            try:
                rl.ImageDraw(
                    atlas_image,
                    source_image,
                    _make_rectangle(0.0, 0.0, placement.width, placement.height),
                    _make_rectangle(
                        float(placement.x),
                        float(placement.y),
                        placement.width,
                        placement.height,
                    ),
                    _make_color(255, 255, 255, 255),
                )
            finally:
                rl.UnloadImage(source_image)

        texture_ref = rl.LoadTextureFromImage(atlas_image[0])
    finally:
        rl.UnloadImage(atlas_image[0])

    atlas_texture = ArepyTexture(texture_ref.id, page_layout.size)
    atlas_texture._ref_texture = texture_ref
    renderer.set_texture_filter(atlas_texture, TextureFilter.NEAREST)
    return atlas_texture


def _require_texture_ref(texture: ArepyTexture) -> object:
    if texture._ref_texture is None:
        raise RuntimeError(
            "Texture atlas building requires loaded raylib textures with a live native reference."
        )
    return texture._ref_texture


def _make_rectangle(x: float, y: float, width: int, height: int) -> object:
    return ffi.new(
        "Rectangle *",
        (float(x), float(y), float(width), float(height)),
    )[0]


def _make_color(r: int, g: int, b: int, a: int) -> object:
    return ffi.new("Color *", (r, g, b, a))[0]


def _validate_source_rect(
    asset_id: str,
    region: TextureAtlasRegion,
    src_x: int,
    src_y: int,
    src_width: int,
    src_height: int,
) -> None:
    if src_x < 0 or src_y < 0:
        raise ValueError(f"Sprite '{asset_id}' has a negative source offset.")
    if src_width <= 0 or src_height <= 0:
        raise ValueError(f"Sprite '{asset_id}' must use a positive source size.")
    if src_x + src_width > region.width or src_y + src_height > region.height:
        raise ValueError(
            f"Sprite '{asset_id}' source rect {(src_x, src_y, src_width, src_height)} exceeds atlas region {(region.width, region.height)}."
        )


__all__ = [
    "TextureAtlas",
    "TextureAtlasCollection",
    "TextureAtlasRegion",
    "TextureBatchGroup",
    "TextureBatchPlan",
    "build_texture_atlas",
]