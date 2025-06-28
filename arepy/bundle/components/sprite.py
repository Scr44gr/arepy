from ...ecs import Component


class Sprite(Component):
    def __init__(
        self,
        asset_id: str,
        src_rect: tuple[int, int, int, int],
        z_index: int,
    ):
        self.asset_id = asset_id
        self.src_rect = src_rect
        self.z_index = z_index
        self.flipped = False
