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


def load_music_from_memory(file_type: str, data: bytes) -> ArepyMusic | None:
    """Load music from memory buffer.
    
    Args:
        file_type: File extension (e.g., ".wav", ".ogg", ".mp3")
        data: Audio data as bytes
    
    Returns:
        ArepyMusic if successful, None otherwise
    """
    from raylib import ffi
    
    # Create buffer from bytes
    data_buffer = ffi.from_buffer(data)
    
    # LoadMusicStreamFromMemory(const char *fileType, const unsigned char *data, int dataSize)
    music = rl.LoadMusicStreamFromMemory(
        file_type.encode("utf-8"), data_buffer, len(data)
    )
    
    # Check if loaded successfully
    if music.frameCount == 0:
        return None
    
    return ArepyMusic(music)


def play_music(music: ArepyMusic) -> None:
    rl.PlayMusicStream(music._ref)  # type: ignore


def is_music_playing(music: ArepyMusic) -> bool:
    return rl.IsMusicPlaying(music._ref)  # type: ignore


def stop_music(music: ArepyMusic) -> None:
    rl.StopMusicStream(music._ref)  # type: ignore


def pause_music(music: ArepyMusic) -> None:
    rl.PauseMusicStream(music._ref)  # type: ignore


def resume_music(music: ArepyMusic) -> None:
    rl.ResumeMusicStream(music._ref)  # type: ignore


def set_music_volume(music: ArepyMusic, volume: float) -> None:
    rl.SetMusicVolume(music._ref, volume)  # type: ignore


def set_music_pitch(music: ArepyMusic, pitch: float) -> None:
    rl.SetMusicPitch(music._ref, pitch)  # type: ignore


def unload_music(music: ArepyMusic) -> None:
    rl.UnloadMusicStream(music._ref)  # type: ignore


def update_music_stream(music: ArepyMusic) -> None:
    """Update music stream buffers. Must be called every frame."""
    rl.UpdateMusicStream(music._ref)  # type: ignore


def get_music_time_length(music: ArepyMusic) -> float:
    """Get music time length in seconds."""
    return rl.GetMusicTimeLength(music._ref)  # type: ignore


def get_music_time_played(music: ArepyMusic) -> float:
    """Get current music time played in seconds."""
    return rl.GetMusicTimePlayed(music._ref)  # type: ignore


def seek_music_stream(music: ArepyMusic, position: float) -> None:
    """Seek music to a position in seconds."""
    rl.SeekMusicStream(music._ref, position)  # type: ignore


def close_device() -> None:
    rl.CloseAudioDevice()
