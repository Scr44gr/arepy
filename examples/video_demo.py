"""
Demo: Video playback with audio using PBO streaming textures

This demonstrates high-performance video playback using:
- PyAV for video decoding
- PBO (Pixel Buffer Objects) for async CPU->GPU texture streaming
- Raylib audio streaming for synchronized audio

Note: Raylib can't extract audio from MP4 containers directly.
      For audio, provide a separate audio file (MP3, OGG, WAV, FLAC)
      or use a video format with supported audio (like OGG/Theora).

Usage:
    Place a video file (mp4, webm, etc.) and optionally an audio file
    with the same name but audio extension (e.g., video.mp4 + video.mp3)
"""

import os

import av

from arepy import ArepyEngine, Renderer2D, SystemPipeline
from arepy.ecs.world import World
from arepy.engine.audio import ArepyMusic, AudioDevice
from arepy.engine.renderer import Color, Rect

# Configuration
VIDEO_PATH = "./gojo.gif"  # Change to your video path
# Audio path - will try to find matching audio file automatically
AUDIO_PATH = None  # Set to explicit path, or None for auto-detection

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Colors
WHITE = Color(255, 255, 255, 255)
BLACK = Color(0, 0, 0, 255)
RED = Color(255, 0, 0, 255)
GRAY = Color(100, 100, 100, 255)

# Global state
video_container = None
video_stream = None
streaming_texture = None
frame_generator = None
video_width = 0
video_height = 0
video_fps = 30.0
frame_time_acc = 0.0

# Audio state
audio_music = None
has_audio = False


def find_audio_file(video_path: str) -> str | None:
    """Try to find a matching audio file for the video."""
    if AUDIO_PATH:
        return AUDIO_PATH if os.path.exists(AUDIO_PATH) else None

    # Try common audio extensions
    base_path = os.path.splitext(video_path)[0]
    audio_extensions = [".mp3", ".ogg", ".wav", ".flac"]

    for ext in audio_extensions:
        audio_path = base_path + ext
        if os.path.exists(audio_path):
            return audio_path

    return None


def extract_audio_from_video(video_path: str) -> bytes | None:
    """Extract audio from video file as WAV bytes using PyAV."""
    import struct

    try:
        container = av.open(video_path)

        # Check if video has audio stream
        if len(container.streams.audio) == 0:
            print("Video has no audio stream")
            container.close()
            return None

        audio_stream = container.streams.audio[0]

        # Collect all audio frames
        audio_data = []
        sample_rate = audio_stream.rate
        channels = audio_stream.channels

        resampler = av.AudioResampler(
            format="s16", layout="stereo" if channels >= 2 else "mono", rate=sample_rate
        )

        for frame in container.decode(audio=0):
            # Resample to s16 format
            resampled = resampler.resample(frame)
            for r in resampled:
                audio_data.append(r.to_ndarray().tobytes())

        container.close()

        if not audio_data:
            print("No audio data extracted")
            return None

        # Build WAV in memory
        raw_audio = b"".join(audio_data)
        num_channels = 2 if channels >= 2 else 1
        sample_width = 2  # 16-bit = 2 bytes

        wav_buffer = bytearray()
        # WAV header
        wav_buffer.extend(b"RIFF")
        wav_buffer.extend(struct.pack("<I", 36 + len(raw_audio)))  # File size - 8
        wav_buffer.extend(b"WAVE")
        wav_buffer.extend(b"fmt ")
        wav_buffer.extend(struct.pack("<I", 16))  # Subchunk1 size
        wav_buffer.extend(struct.pack("<H", 1))  # Audio format (1 = PCM)
        wav_buffer.extend(struct.pack("<H", num_channels))
        wav_buffer.extend(struct.pack("<I", sample_rate))
        wav_buffer.extend(
            struct.pack("<I", sample_rate * num_channels * sample_width)
        )  # Byte rate
        wav_buffer.extend(struct.pack("<H", num_channels * sample_width))  # Block align
        wav_buffer.extend(struct.pack("<H", sample_width * 8))  # Bits per sample
        wav_buffer.extend(b"data")
        wav_buffer.extend(struct.pack("<I", len(raw_audio)))
        wav_buffer.extend(raw_audio)

        print(f"Extracted audio: {len(wav_buffer)} bytes in memory")
        return bytes(wav_buffer)

    except Exception as e:
        print(f"Failed to extract audio: {e}")
        return None


# Track audio data in memory (keep reference to prevent GC)
audio_memory_data = None


def init_video(renderer: Renderer2D, audio: AudioDevice) -> bool:
    """Initialize video, streaming texture, and audio."""
    global video_container, video_stream, streaming_texture
    global frame_generator, video_width, video_height, video_fps
    global audio_music, has_audio, audio_memory_data

    try:
        # Open video file
        video_container = av.open(VIDEO_PATH)
        video_stream = video_container.streams.video[0]

        video_width = video_stream.width
        video_height = video_stream.height
        video_fps = (
            float(video_stream.average_rate) if video_stream.average_rate else 30.0
        )

        print(f"Video: {video_width}x{video_height} @ {video_fps:.2f} fps")

        # Initialize streaming
        if not renderer.is_streaming_available():
            renderer.init_streaming()

        if not renderer.is_streaming_available():
            print("Failed to initialize PBO streaming")
            return False

        # Create streaming texture (RGBA = 4 channels)
        streaming_texture = renderer.create_streaming_texture(
            video_width, video_height, 4
        )
        if streaming_texture is None:
            print("Failed to create streaming texture")
            return False

        # Create frame generator
        frame_generator = video_container.decode(video=0)

        # Try to load audio
        # 1. First look for separate audio file
        audio_path = find_audio_file(VIDEO_PATH)

        if audio_path:
            # Load from file
            try:
                from pathlib import Path

                audio_music = audio.load_music(Path(audio_path))
                audio.play_music(audio_music)
                has_audio = True
                print(f"Audio loaded from file: {audio_path}")
            except Exception as e:
                print(f"Failed to load audio file: {e}")
                has_audio = False
        else:
            # 2. Extract from video and load from memory (no temp file!)
            print("No separate audio file, extracting from video to memory...")
            audio_memory_data = extract_audio_from_video(VIDEO_PATH)

            if audio_memory_data:
                audio_music = audio.load_music_from_memory(".wav", audio_memory_data)
                if audio_music:
                    audio.play_music(audio_music)
                    has_audio = True
                    print("Audio loaded from memory and playing!")
                else:
                    has_audio = False
            else:
                print("No audio available for this video")
                has_audio = False

        print("Video initialized successfully!")
        return True

    except Exception as e:
        print(f"Failed to initialize video: {e}")
        return False


def get_next_frame(audio: AudioDevice | None = None):
    """Get the next video frame as RGBA bytes."""
    global frame_generator, video_container, audio_music, has_audio

    try:
        frame = next(frame_generator)
        # Convert to RGBA (4 channels for OpenGL)
        rgba_frame = frame.to_ndarray(format="rgba")
        return rgba_frame.tobytes()
    except StopIteration:
        # Loop video - seek to beginning
        video_container.seek(0)
        frame_generator = video_container.decode(video=0)

        # Also seek audio to beginning
        if audio and has_audio and audio_music:
            audio.seek_music_stream(audio_music, 0.0)

        try:
            frame = next(frame_generator)
            rgba_frame = frame.to_ndarray(format="rgba")
            return rgba_frame.tobytes()
        except:
            return None
    except Exception as e:
        print(f"Error getting frame: {e}")
        return None


video_initialized = False


def render_system(renderer: Renderer2D, audio: AudioDevice) -> None:
    """Render system for video playback."""
    global video_initialized, frame_time_acc, streaming_texture, audio_music, has_audio

    renderer.start_frame()
    renderer.clear(BLACK)

    # Initialize video on first frame
    if not video_initialized:
        video_initialized = init_video(renderer, audio)

    if video_initialized and streaming_texture:
        delta_time = renderer.get_delta_time()
        frame_time_acc += delta_time

        # Update audio stream (IMPORTANT: must be called every frame)
        if has_audio and audio_music:
            audio.update_music_stream(audio_music)

        # Update video frame at video FPS
        frame_duration = 1.0 / video_fps
        if frame_time_acc >= frame_duration:
            frame_time_acc -= frame_duration

            # Get next frame and update texture
            pixels = get_next_frame(audio)
            if pixels:
                renderer.update_streaming_texture(streaming_texture, pixels)

        # Get the texture for drawing
        texture = renderer.get_streaming_texture(streaming_texture)

        # Calculate destination rect to fit window while maintaining aspect ratio
        video_aspect = video_width / video_height
        window_aspect = WINDOW_WIDTH / WINDOW_HEIGHT

        if video_aspect > window_aspect:
            # Video is wider - fit to width
            dst_width = WINDOW_WIDTH
            dst_height = int(WINDOW_WIDTH / video_aspect)
        else:
            # Video is taller - fit to height
            dst_height = WINDOW_HEIGHT
            dst_width = int(WINDOW_HEIGHT * video_aspect)

        # Center the video
        dst_x = (WINDOW_WIDTH - dst_width) // 2
        dst_y = (WINDOW_HEIGHT - dst_height) // 2

        # Draw video using draw_texture_ex for proper scaling
        src_rect = Rect(0, 0, video_width, video_height)
        dst_rect = Rect(dst_x, dst_y, dst_width, dst_height)
        renderer.draw_texture_ex(texture, src_rect, dst_rect, (0, 0), 0.0, WHITE)

        # Draw info
        renderer.draw_text(f"Video: {video_width}x{video_height}", (10, 10), 16, WHITE)
        renderer.draw_text(f"FPS: {renderer.get_framerate()}", (10, 30), 16, WHITE)
        renderer.draw_text("PBO Streaming Enabled", (10, 50), 16, WHITE)

        # Show audio status
        if has_audio and audio_music:
            time_played = audio.get_music_time_played(audio_music)
            time_length = audio.get_music_time_length(audio_music)

            renderer.draw_text(
                f"Audio: {time_played:.1f}s / {time_length:.1f}s", (10, 70), 16, WHITE
            )

            # Draw progress bar
            bar_width = 200
            bar_height = 8
            bar_x = 10
            bar_y = 90
            progress = time_played / time_length if time_length > 0 else 0
            renderer.draw_rectangle(Rect(bar_x, bar_y, bar_width, bar_height), GRAY)
            renderer.draw_rectangle(
                Rect(bar_x, bar_y, int(bar_width * progress), bar_height), WHITE
            )
        else:
            renderer.draw_text("Audio: None", (10, 70), 16, GRAY)
    else:
        renderer.draw_text("Failed to load video", (10, 10), 20, RED)
        renderer.draw_text(f"Path: {VIDEO_PATH}", (10, 40), 16, WHITE)

    renderer.end_frame()


def cleanup(audio: AudioDevice | None = None):
    """Clean up resources."""
    global video_container, streaming_texture, audio_music, has_audio, audio_memory_data

    # Unload audio
    if audio and has_audio and audio_music:
        audio.stop_music(audio_music)
        audio.unload_music(audio_music)

    if video_container:
        video_container.close()

    # Clear memory data reference
    audio_memory_data = None

    # Note: streaming_texture cleanup would be done by renderer


def main():
    engine = ArepyEngine(
        title="Video Playback Demo (PBO Streaming)",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        vsync=True,
    )

    world: World = engine.create_world("main")
    world.add_system(SystemPipeline.RENDER, render_system)

    engine.set_current_world("main")
    engine.run()

    cleanup(engine.audio_device)


if __name__ == "__main__":
    main()
