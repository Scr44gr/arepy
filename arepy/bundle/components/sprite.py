from ...ecs import Component
from ._field_views import InternedStringTable, assign_fields, field_tuple

_ASSET_IDS = InternedStringTable()


class Sprite(Component):
    asset_id_handle: int
    src_x: int
    src_y: int
    src_w: int
    src_h: int
    z_index: int
    flipped: bool

    def __init__(
        self,
        asset_id: str,
        src_rect: tuple[int, int, int, int],
        z_index: int,
    ):
        super().__init__()
        self.asset_id = asset_id
        self.src_rect = src_rect
        self.z_index = z_index
        self.flipped = False

    @property
    def asset_id(self) -> object:
        return _ASSET_IDS.resolve(self.asset_id_handle)

    @asset_id.setter
    def asset_id(self, value: str) -> None:
        self.asset_id_handle = _ASSET_IDS.intern(value)

    @property
    def src_rect(self) -> tuple[object, object, object, object]:
        return field_tuple(self, "src_x", "src_y", "src_w", "src_h")

    @src_rect.setter
    def src_rect(self, value: tuple[int, int, int, int]) -> None:
        assign_fields(self, value, "src_x", "src_y", "src_w", "src_h")
