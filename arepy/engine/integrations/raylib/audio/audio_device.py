from os import PathLike

import raylib as rl

from arepy.engine.audio import ArepyMusic, ArepySound


def init_device() -> None:
    rl.InitAudioDevice()


def load_sound(path: PathLike[str]) -> ArepySound:
    return ArepySound(rl.LoadSound(str(path).encode("utf-8")))


def play_sound(sound: ArepySound) -> None:
    rl.PlaySound(sound._ref)  # type: ignore


def is_sound_playing(sound: ArepySound) -> bool:
    return rl.IsSoundPlaying(sound._ref)  # type: ignore


def stop_sound(sound: ArepySound) -> None:
    rl.StopSound(sound._ref)  # type: ignore


def resume_sound(sound: ArepySound) -> None:
    rl.ResumeSound(sound._ref)  # type: ignore


def set_sound_pitch(sound: ArepySound, pitch: float) -> None:
    rl.SetSoundPitch(sound._ref, pitch)  # type: ignore


def set_sound_volume(sound: ArepySound, volume: float) -> None:
    rl.SetSoundVolume(sound._ref, volume)  # type: ignore


def unload_sound(sound: ArepySound) -> None:
    rl.UnloadSound(sound._ref)  # type: ignore


def load_music(path: PathLike[str]) -> ArepyMusic:
    return ArepyMusic(rl.LoadMusicStream(str(path).encode("utf-8")))


def play_music(music: ArepyMusic) -> None:
    rl.PlayMusicStream(music._ref)  # type: ignore


def is_music_playing(music: ArepyMusic) -> bool:
    return rl.IsMusicPlaying(music._ref)  # type: ignore


def stop_music(music: ArepyMusic) -> None:
    rl.StopMusicStream(music._ref)  # type: ignore


def resume_music(music: ArepyMusic) -> None:
    rl.ResumeMusicStream(music._ref)  # type: ignore


def set_music_volume(music: ArepyMusic, volume: float) -> None:
    rl.SetMusicVolume(music._ref, volume)  # type: ignore


def set_music_pitch(music: ArepyMusic, pitch: float) -> None:
    rl.SetMusicPitch(music._ref, pitch)  # type: ignore


def unload_music(music: ArepyMusic) -> None:
    rl.UnloadMusicStream(music._ref)  # type: ignore


def close_device() -> None:
    rl.CloseAudioDevice()
