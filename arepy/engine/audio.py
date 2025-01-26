from os import PathLike
from typing import Protocol


class ArepySound:
    def __init__(self, ref: object):
        self._ref = ref

    def unload(self) -> None: ...


class ArepyMusic:
    def __init__(self, ref: object):
        self._ref = ref

    def unload(self) -> None: ...


class AudioDevice(Protocol):

    def init_device(self) -> None: ...

    # Sounds
    def load_sound(self, path: PathLike[str]) -> ArepySound: ...
    def play_sound(self, sound: ArepySound) -> None: ...
    def is_sound_playing(self, sound: ArepySound) -> bool: ...
    def stop_sound(self, sound: ArepySound) -> None: ...
    def resume_sound(self, sound: ArepySound) -> None: ...
    def set_sound_pitch(self, sound: ArepySound, pitch: float) -> None: ...
    def set_sound_volume(self, sound: ArepySound, volume: float) -> None: ...
    def unload_sound(self, sound: ArepySound) -> None: ...

    # Music
    def load_music(self, path: PathLike[str]) -> ArepyMusic: ...
    def play_music(self, music: ArepyMusic) -> None: ...
    def is_music_playing(self, music: ArepyMusic) -> bool: ...
    def stop_music(self, music: ArepyMusic) -> None: ...
    def resume_music(self, music: ArepyMusic) -> None: ...
    def set_music_volume(self, music: ArepyMusic, volume: float) -> None: ...
    def set_music_pitch(self, music: ArepyMusic, pitch: float) -> None: ...
    def unload_music(self, music: ArepyMusic) -> None: ...
    def close_device(self) -> None: ...
