from arepy.ecs.components import Component


class Animation(Component):
    def __init__(
        self,
        current_frame: int,
        frame_count: int,
        frame_speed_rate: int,
        start_time: float,
        is_playing: bool,
        repeat: bool,
    ) -> None:
        self.current_frame = current_frame
        self.frame_count = frame_count
        self.frame_speed_rate = frame_speed_rate
        self.start_time = start_time
        self.is_playing = is_playing
        self.repeat = repeat
