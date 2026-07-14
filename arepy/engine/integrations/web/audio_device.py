"""Conservative browser audio adapter.

The initial web backend keeps the protocol available while full WebAudio asset
streaming is developed independently from the builder.
"""

from arepy.engine.audio import ArepyMusic, ArepySound


def init_device() -> None:
    return None


def close_device() -> None:
    return None


def load_sound(path: object) -> ArepySound:
    return ArepySound(path)


def load_music(path: object) -> ArepyMusic:
    return ArepyMusic(path)


def load_music_from_memory(file_type: str, data: bytes) -> ArepyMusic:
    return ArepyMusic(data)


def play_sound(sound: ArepySound) -> None:
    return None


def is_sound_playing(sound: ArepySound) -> bool:
    return False


def stop_sound(sound: ArepySound) -> None:
    return None


resume_sound = stop_sound
unload_sound = stop_sound


def set_sound_pitch(sound: ArepySound, pitch: float) -> None:
    return None


def set_sound_volume(sound: ArepySound, volume: float) -> None:
    return None


def play_music(music: ArepyMusic) -> None:
    return None


def is_music_playing(music: ArepyMusic) -> bool:
    return False


def stop_music(music: ArepyMusic) -> None:
    return None


pause_music = stop_music
resume_music = stop_music


def set_music_volume(music: ArepyMusic, volume: float) -> None:
    return None


def set_music_pitch(music: ArepyMusic, pitch: float) -> None:
    return None


unload_music = stop_music
update_music_stream = stop_music


def get_music_time_length(music: ArepyMusic) -> float:
    return 0.0


def get_music_time_played(music: ArepyMusic) -> float:
    return 0.0


def seek_music_stream(music: ArepyMusic, position: float) -> None:
    return None
