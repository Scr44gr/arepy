"""A self-contained sound-effect example for Arepy.

The demo creates a short WAV tone once during world startup, loads it through
``AssetStore`` and ``AudioDevice``, and then removes the temporary source file.
All drawing colors and rectangles are allocated up front and reused.
"""

from __future__ import annotations

from math import pi, sin
from pathlib import Path
from struct import pack_into
from tempfile import NamedTemporaryFile
import wave

from arepy import (
    ArepyEngine,
    AudioDevice,
    Color,
    Input,
    Key,
    Rect,
    Renderer2D,
    SystemPipeline,
    Time,
    WindowFlag,
)
from arepy.asset_store import AssetStore
from arepy.engine.audio import ArepySound

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
SOUND_NAME = "demo_tone"
TONE_FREQUENCY_HZ = 523.25
TONE_DURATION_SECONDS = 0.34
SAMPLE_RATE = 44_100

MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
VOLUME_STEP = 0.1
MIN_PITCH = 0.5
MAX_PITCH = 2.0
PITCH_STEP = 0.1
CONTROL_TRACK_WIDTH = 312

# Palette: values are shared across every frame.
BACKGROUND_TOP = Color(12, 18, 35, 255)
BACKGROUND_BOTTOM = Color(27, 37, 65, 255)
CARD = Color(22, 31, 54, 244)
CARD_OUTLINE = Color(63, 79, 119, 255)
TEXT = Color(239, 244, 255, 255)
MUTED = Color(159, 173, 205, 255)
ACCENT = Color(115, 224, 209, 255)
ACCENT_SOFT = Color(48, 114, 113, 255)
ACTIVE = Color(135, 235, 168, 255)
INACTIVE = Color(98, 111, 145, 255)
TRACK = Color(42, 54, 83, 255)
PITCH_COLOR = Color(148, 163, 255, 255)
KEY_BACKGROUND = Color(32, 43, 72, 255)
KEY_ACTIVE = Color(53, 72, 109, 255)
WAVE = Color(92, 184, 184, 255)
SHADOW = Color(2, 5, 13, 100)

# Geometry is also shared. The only mutable rectangles live in AudioDemoState.
BACKGROUND = Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
SHADOW_CARD = Rect(31, 113, 898, 374)
MAIN_CARD = Rect(32, 108, 896, 374)
VISUAL_CARD = Rect(56, 136, 370, 318)
CONTROL_CARD = Rect(450, 136, 454, 318)
STATUS_PILL = Rect(80, 166, 126, 32)
VOLUME_TRACK = Rect(482, 240, CONTROL_TRACK_WIDTH, 16)
PITCH_TRACK = Rect(482, 322, CONTROL_TRACK_WIDTH, 16)
SPACE_KEY = Rect(482, 385, 154, 42)
ARROW_KEY = Rect(650, 385, 222, 42)
SPEAKER_CENTER = (241.0, 288.0)

# A small waveform decoration built once when the module is imported.
WAVE_POINTS = [
    (
        92.0 + index * 7.5,
        385.0 + sin(index * 0.72) * (18.0 - abs(index - 16) * 0.35),
    )
    for index in range(33)
]


class AudioDemoState:
    """Mutable UI and sound state reused by all systems."""

    __slots__ = (
        "sound",
        "volume",
        "pitch",
        "play_count",
        "volume_fill",
        "pitch_fill",
        "volume_label",
        "pitch_label",
        "plays_label",
        "status_label",
    )

    def __init__(self) -> None:
        self.sound: ArepySound | None = None
        self.volume = 0.7
        self.pitch = 1.0
        self.play_count = 0
        self.volume_fill = Rect(
            VOLUME_TRACK.x,
            VOLUME_TRACK.y,
            int(CONTROL_TRACK_WIDTH * self.volume),
            VOLUME_TRACK.height,
        )
        self.pitch_fill = Rect(
            PITCH_TRACK.x,
            PITCH_TRACK.y,
            int(CONTROL_TRACK_WIDTH * self._normalized_pitch()),
            PITCH_TRACK.height,
        )
        self.volume_label = "Volume 70%"
        self.pitch_label = "Pitch 1.00x"
        self.plays_label = "Played 0 times"
        self.status_label = "READY"

    def update_volume(self, value: float) -> None:
        self.volume = min(MAX_VOLUME, max(MIN_VOLUME, value))
        self.volume_fill.width = int(CONTROL_TRACK_WIDTH * self.volume)
        self.volume_label = f"Volume {self.volume:.0%}"

    def update_pitch(self, value: float) -> None:
        self.pitch = min(MAX_PITCH, max(MIN_PITCH, value))
        self.pitch_fill.width = int(
            CONTROL_TRACK_WIDTH * self._normalized_pitch()
        )
        self.pitch_label = f"Pitch {self.pitch:.2f}x"

    def record_play(self) -> None:
        self.play_count += 1
        suffix = "time" if self.play_count == 1 else "times"
        self.plays_label = f"Played {self.play_count} {suffix}"

    def _normalized_pitch(self) -> float:
        return (self.pitch - MIN_PITCH) / (MAX_PITCH - MIN_PITCH)


def _write_tone_wav(path: Path) -> None:
    """Write a short mono tone with fades to avoid clicks at either edge."""

    frame_count = int(SAMPLE_RATE * TONE_DURATION_SECONDS)
    fade_frames = int(SAMPLE_RATE * 0.018)
    pcm = bytearray(frame_count * 2)
    radians_per_frame = 2.0 * pi * TONE_FREQUENCY_HZ / SAMPLE_RATE

    for frame in range(frame_count):
        fade_in = min(1.0, frame / fade_frames)
        fade_out = min(1.0, (frame_count - frame - 1) / fade_frames)
        envelope = min(fade_in, fade_out)
        sample = int(32_767 * 0.38 * envelope * sin(frame * radians_per_frame))
        pack_into("<h", pcm, frame * 2, sample)

    with wave.open(str(path), "wb") as tone_file:
        tone_file.setnchannels(1)
        tone_file.setsampwidth(2)
        tone_file.setframerate(SAMPLE_RATE)
        tone_file.writeframes(pcm)


def load_demo_sound(
    assets: AssetStore,
    audio_device: AudioDevice,
    state: AudioDemoState,
) -> None:
    """Generate and load the sound once when the world starts."""

    with NamedTemporaryFile(
        prefix="arepy-audio-demo-",
        suffix=".wav",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        _write_tone_wav(temporary_path)
        assets.load_sound(audio_device, SOUND_NAME, str(temporary_path))
        state.sound = assets.get_sound(SOUND_NAME)
        audio_device.set_sound_volume(state.sound, state.volume)
        audio_device.set_sound_pitch(state.sound, state.pitch)
    finally:
        # Short sounds are decoded into memory by Arepy's desktop backend.
        # Music is streamed and should keep its source file instead.
        temporary_path.unlink(missing_ok=True)


def handle_audio_input(
    input_device: Input,
    audio_device: AudioDevice,
    state: AudioDemoState,
) -> None:
    """Translate one-frame key presses into sound controls."""

    sound = state.sound
    if sound is None:
        return

    if input_device.is_key_pressed(Key.SPACE):
        audio_device.play_sound(sound)
        state.record_play()

    if input_device.is_key_pressed(Key.UP):
        state.update_volume(state.volume + VOLUME_STEP)
        audio_device.set_sound_volume(sound, state.volume)
    elif input_device.is_key_pressed(Key.DOWN):
        state.update_volume(state.volume - VOLUME_STEP)
        audio_device.set_sound_volume(sound, state.volume)

    if input_device.is_key_pressed(Key.RIGHT):
        state.update_pitch(state.pitch + PITCH_STEP)
        audio_device.set_sound_pitch(sound, state.pitch)
    elif input_device.is_key_pressed(Key.LEFT):
        state.update_pitch(state.pitch - PITCH_STEP)
        audio_device.set_sound_pitch(sound, state.pitch)


def render_audio_demo(
    renderer: Renderer2D,
    audio_device: AudioDevice,
    time: Time,
    state: AudioDemoState,
) -> None:
    """Draw the audio playground without allocating render values per frame."""

    sound = state.sound
    is_playing = sound is not None and audio_device.is_sound_playing(sound)
    state.status_label = "PLAYING" if is_playing else "READY"
    status_color = ACTIVE if is_playing else INACTIVE
    speaker_color = ACCENT if is_playing else ACCENT_SOFT
    pulse = (sin(time.elapsed_seconds * 10.0) + 1.0) * 0.5 if is_playing else 0.0

    renderer.start_frame()
    renderer.draw_rectangle_gradient_v(
        BACKGROUND,
        BACKGROUND_TOP,
        BACKGROUND_BOTTOM,
    )

    renderer.draw_text("AREPY AUDIO PLAYGROUND", (32, 26), 28, TEXT)
    renderer.draw_text(
        "Load once, trigger many times, release when the world closes.",
        (32, 64),
        18,
        MUTED,
    )

    renderer.draw_rectangle_rounded(SHADOW_CARD, 0.06, 8, SHADOW)
    renderer.draw_rectangle_rounded(MAIN_CARD, 0.06, 8, CARD)
    renderer.draw_rectangle_rounded_lines(MAIN_CARD, 0.06, 8, CARD_OUTLINE)

    renderer.draw_rectangle_rounded(VISUAL_CARD, 0.08, 8, KEY_BACKGROUND)
    renderer.draw_text("SHORT SOUND", (80, 148), 16, MUTED)
    renderer.draw_rectangle_rounded(STATUS_PILL, 0.5, 10, TRACK)
    renderer.draw_circle((94.0, 182.0), 5.0, status_color)
    renderer.draw_text(state.status_label, (108, 173), 16, status_color)

    renderer.draw_circle(SPEAKER_CENTER, 70.0 + pulse * 7.0, TRACK)
    renderer.draw_circle(SPEAKER_CENTER, 49.0 + pulse * 4.0, speaker_color)
    renderer.draw_circle(SPEAKER_CENTER, 20.0, CARD)
    renderer.draw_text("A", (232, 271), 31, TEXT)
    renderer.draw_lines(WAVE_POINTS, WAVE)
    renderer.draw_text(state.plays_label, (80, 414), 16, MUTED)

    renderer.draw_rectangle_rounded(CONTROL_CARD, 0.08, 8, KEY_BACKGROUND)
    renderer.draw_text("LIVE CONTROLS", (482, 158), 16, MUTED)
    renderer.draw_text(state.volume_label, (482, 205), 20, TEXT)
    renderer.draw_rectangle_rounded(VOLUME_TRACK, 0.5, 8, TRACK)
    renderer.draw_rectangle_rounded(state.volume_fill, 0.5, 8, ACCENT)

    renderer.draw_text(state.pitch_label, (482, 287), 20, TEXT)
    renderer.draw_rectangle_rounded(PITCH_TRACK, 0.5, 8, TRACK)
    renderer.draw_rectangle_rounded(state.pitch_fill, 0.5, 8, PITCH_COLOR)

    renderer.draw_rectangle_rounded(SPACE_KEY, 0.18, 8, KEY_ACTIVE)
    renderer.draw_text("SPACE", (520, 397), 18, TEXT)
    renderer.draw_rectangle_rounded(ARROW_KEY, 0.18, 8, KEY_ACTIVE)
    renderer.draw_text("ARROW KEYS", (688, 397), 18, TEXT)
    renderer.draw_text("play tone", (518, 435), 14, MUTED)
    renderer.draw_text("volume / pitch", (690, 435), 14, MUTED)

    renderer.draw_fps((WINDOW_WIDTH - 96, 24))
    renderer.end_frame()


def main() -> None:
    engine = ArepyEngine(
        title="Arepy audio playground",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        max_frame_rate=0,
        window_flags=WindowFlag.VSYNC_HINT,
    )
    world = engine.create_world("audio_demo")
    state = AudioDemoState()
    world.add_resource(state)

    assets = engine.get_resource(AssetStore)
    audio_device = engine.get_resource(AudioDevice)

    @world.on_startup
    def setup_audio() -> None:
        load_demo_sound(assets, audio_device, state)

    @world.on_shutdown
    def unload_audio() -> None:
        if state.sound is not None:
            assets.unload_sound(audio_device, SOUND_NAME)
            state.sound = None

    world.add_system(SystemPipeline.INPUT, handle_audio_input)
    world.add_system(SystemPipeline.RENDER, render_audio_demo)
    engine.set_current_world("audio_demo")
    engine.run()


if __name__ == "__main__":
    main()
