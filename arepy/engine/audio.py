"""Public audio protocol and lightweight wrappers for sounds and music."""

from os import PathLike
from typing import Protocol, runtime_checkable


class ArepySound:
    """Wrapper around a short sound effect handle."""

    def __init__(self, ref: object):
        self._ref = ref

    def unload(self) -> None:
        """Release the sound from memory."""
        ...


class ArepyMusic:
    """Wrapper around a streamed music handle."""

    def __init__(self, ref: object):
        self._ref = ref

    def unload(self) -> None:
        """Release the music stream from memory."""
        ...


@runtime_checkable
class AudioDevice(Protocol):
    """Protocol defining sound and music playback operations.

    The engine registers one `AudioDevice` implementation as a shared resource,
    so systems can trigger sound effects or music through type-based injection.
    """

    def init_device(self) -> None:
        """Initialize the audio backend before playing sounds or music."""
        ...

    # Sounds
    def load_sound(self, path: PathLike[str]) -> ArepySound:
        """Load a short sound effect from disk."""
        ...

    def play_sound(self, sound: ArepySound) -> None:
        """Play a sound effect once."""
        ...

    def is_sound_playing(self, sound: ArepySound) -> bool:
        """Return whether a sound effect is currently playing."""
        ...

    def stop_sound(self, sound: ArepySound) -> None:
        """Stop a sound effect immediately."""
        ...

    def resume_sound(self, sound: ArepySound) -> None:
        """Resume a paused sound effect."""
        ...

    def set_sound_pitch(self, sound: ArepySound, pitch: float) -> None:
        """Change the playback pitch of a sound effect."""
        ...

    def set_sound_volume(self, sound: ArepySound, volume: float) -> None:
        """Change the playback volume of a sound effect."""
        ...

    def unload_sound(self, sound: ArepySound) -> None:
        """Release a loaded sound effect."""
        ...

    # Music
    def load_music(self, path: PathLike[str]) -> ArepyMusic:
        """Load a streamed music track from disk."""
        ...

    def load_music_from_memory(self, file_type: str, data: bytes) -> ArepyMusic | None:
        """Load a music stream from bytes already in memory."""
        ...

    def play_music(self, music: ArepyMusic) -> None:
        """Start playback of a music stream."""
        ...

    def is_music_playing(self, music: ArepyMusic) -> bool:
        """Return whether a music stream is currently playing."""
        ...

    def stop_music(self, music: ArepyMusic) -> None:
        """Stop a music stream immediately."""
        ...

    def pause_music(self, music: ArepyMusic) -> None:
        """Pause a music stream."""
        ...

    def resume_music(self, music: ArepyMusic) -> None:
        """Resume a paused music stream."""
        ...

    def set_music_volume(self, music: ArepyMusic, volume: float) -> None:
        """Change the playback volume of a music stream."""
        ...

    def set_music_pitch(self, music: ArepyMusic, pitch: float) -> None:
        """Change the playback pitch of a music stream."""
        ...

    def unload_music(self, music: ArepyMusic) -> None:
        """Release a loaded music stream."""
        ...

    def update_music_stream(self, music: ArepyMusic) -> None:
        """Advance streaming buffers for long-running music playback."""
        ...

    def get_music_time_length(self, music: ArepyMusic) -> float:
        """Return the total length of a music stream in seconds."""
        ...

    def get_music_time_played(self, music: ArepyMusic) -> float:
        """Return how many seconds of the track have already played."""
        ...

    def seek_music_stream(self, music: ArepyMusic, position: float) -> None:
        """Seek to a playback position in seconds."""
        ...

    def close_device(self) -> None:
        """Shut down the audio backend and release device resources."""
        ...


__all_ = ["AudioDevice", "ArepySound", "ArepyMusic"]
