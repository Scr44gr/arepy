from ...ecs import Component


class Sprite(Component):
    _layout_revision = 0

    def __init__(
        self,
        asset_id: str,
        src_rect: tuple[int, int, int, int],
        z_index: int,
    ):
        object.__setattr__(self, "asset_id", asset_id)
        object.__setattr__(self, "src_rect", src_rect)
        object.__setattr__(self, "z_index", z_index)
        object.__setattr__(self, "flipped", False)
        Sprite._layout_revision += 1

    def __setattr__(self, name: str, value: object) -> None:
        if name in ("asset_id", "src_rect"):
            previous = self.__dict__.get(name)
            object.__setattr__(self, name, value)
            if previous != value:
                Sprite._layout_revision += 1
            return
        object.__setattr__(self, name, value)

    @classmethod
    def get_layout_revision(cls) -> int:
        return Sprite._layout_revision
