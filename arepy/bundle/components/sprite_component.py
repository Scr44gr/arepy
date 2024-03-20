from ...ecs import Component


class Sprite(Component):
    def __init__(
        self,
        width: int,
        height: int,
        asset_id: str,
        src_rect: tuple[int, int],
        z_index: int,
    ):
        self.width = width
        self.height = height
        self.asset_id = asset_id
        self.src_rect: list = [width, height, src_rect[0], src_rect[1]]
        self.z_index = z_index
