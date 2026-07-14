"""Play a local video through Arepy's PBO streaming texture API.

The file is intentionally supplied on the command line: the repository does not
ship a large sample video. Install the optional dependency and run, for example::

    uv sync --extra video
    uv run python examples/video_demo.py path/to/clip.mp4
    uv run python examples/video_demo.py path/to/clip.mp4 --audio path/to/clip.ogg

When ``--audio`` is omitted, the demo looks for a sidecar audio file with the
same stem. Raylib cannot play an audio track straight from an MP4 container, so
embedded audio is not silently extracted into a large in-memory WAV. A sidecar
starts with the video and is rewound on a loop, but this small demo does not
implement clock-drift correction.

Video decoding still creates a PyAV frame. For tightly packed RGBA output, the
Raylib backend consumes a ``memoryview`` while that frame remains alive, avoiding
an additional full-frame ``bytes`` allocation. If PyAV adds row padding, the
rows are copied into one reusable ``bytearray``. The streaming upload copies the
view synchronously into its PBO, so the view is never retained by the renderer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence

from arepy import ArepyEngine, Renderer2D, SystemPipeline, WindowFlag
from arepy.ecs.world import World
from arepy.engine.audio import ArepyMusic, AudioDevice
from arepy.engine.renderer import ArepyTexture, Color, Rect

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
AUDIO_EXTENSIONS = (".ogg", ".mp3", ".wav", ".flac")
MAX_DECODE_STEPS = 4
HUD_REFRESH_SECONDS = 0.25

WHITE = Color(255, 255, 255, 255)
BLACK = Color(8, 10, 16, 255)
GRAY = Color(100, 108, 124, 255)
RED = Color(232, 84, 84, 255)
VIDEO_ORIGIN = (0, 0)
VIDEO_TEXT_POSITION = (10, 10)
FPS_TEXT_POSITION = (10, 30)
STREAMING_TEXT_POSITION = (10, 50)
AUDIO_TEXT_POSITION = (10, 70)
STATUS_TEXT_POSITION = (10, 110)


class DemoConfig:
    """Validated command-line settings."""

    __slots__ = ("video_path", "audio_path", "loop")

    def __init__(
        self, video_path: Path, audio_path: Path | None, loop: bool
    ) -> None:
        self.video_path = video_path
        self.audio_path = audio_path
        self.loop = loop


def _sidecar_audio(video_path: Path) -> Path | None:
    for extension in AUDIO_EXTENSIONS:
        candidate = video_path.with_suffix(extension)
        if candidate.is_file():
            return candidate
    return None


def parse_args(argv: Sequence[str] | None = None) -> DemoConfig:
    parser = argparse.ArgumentParser(
        description="Play a local video with Arepy PBO texture streaming."
    )
    parser.add_argument("video", type=Path, help="video file decoded by PyAV")
    audio_group = parser.add_mutually_exclusive_group()
    audio_group.add_argument(
        "--audio",
        type=Path,
        help="optional Raylib-compatible sidecar audio file",
    )
    audio_group.add_argument(
        "--silent",
        action="store_true",
        help="disable sidecar discovery and play video only",
    )
    parser.add_argument(
        "--no-loop",
        action="store_true",
        help="stop on the final video frame instead of looping",
    )
    args = parser.parse_args(argv)

    video_path = args.video.expanduser().resolve()
    if not video_path.is_file():
        parser.error(f"video file does not exist: {video_path}")

    audio_path: Path | None
    if args.silent:
        audio_path = None
    elif args.audio is not None:
        audio_path = args.audio.expanduser().resolve()
        if not audio_path.is_file():
            parser.error(f"audio file does not exist: {audio_path}")
    else:
        audio_path = _sidecar_audio(video_path)

    return DemoConfig(video_path, audio_path, not args.no_loop)


def _load_pyav() -> ModuleType:
    try:
        import av
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyAV is required for this example. Install it with "
            "`uv sync --extra video`."
        ) from exc
    return av


class VideoPlayer:
    """Long-lived playback state injected into update and render systems."""

    __slots__ = (
        "video_path",
        "audio_path",
        "loop",
        "width",
        "height",
        "fps",
        "frame_duration",
        "frame_accumulator",
        "hud_accumulator",
        "video_label",
        "fps_label",
        "audio_label",
        "status_label",
        "source",
        "destination",
        "progress_track",
        "progress_fill",
        "_container",
        "_video_stream",
        "_frames",
        "_streaming",
        "_texture",
        "_music",
        "_audio_started",
        "_audio_length",
        "_rgba_frame",
        "_frame_view",
        "_tight_buffer",
        "_tight_view",
        "_row_bytes",
        "_pixel_count",
        "_finished",
        "_closed",
    )

    def __init__(self, config: DemoConfig) -> None:
        self.video_path = config.video_path
        self.audio_path = config.audio_path
        self.loop = config.loop
        self.width = 0
        self.height = 0
        self.fps = 30.0
        self.frame_duration = 1.0 / self.fps
        self.frame_accumulator = 0.0
        self.hud_accumulator = HUD_REFRESH_SECONDS
        self.video_label = "Video: not initialized"
        self.fps_label = "Window: -- FPS"
        self.audio_label = "Audio: none"
        self.status_label = ""
        self.source = Rect(0, 0, 0, 0)
        self.destination = Rect(0, 0, 0, 0)
        self.progress_track = Rect(10, 92, 240, 8)
        self.progress_fill = Rect(10, 92, 0, 8)
        self._container: Any | None = None
        self._video_stream: Any | None = None
        self._frames: Any | None = None
        self._streaming: object | None = None
        self._texture: ArepyTexture | None = None
        self._music: ArepyMusic | None = None
        self._audio_started = False
        self._audio_length = 0.0
        self._rgba_frame: Any | None = None
        self._frame_view: memoryview | None = None
        self._tight_buffer: bytearray | None = None
        self._tight_view: memoryview | None = None
        self._row_bytes = 0
        self._pixel_count = 0
        self._finished = False
        self._closed = False

    def initialize(
        self, pyav: ModuleType, renderer: Renderer2D, audio: AudioDevice
    ) -> None:
        """Open all CPU/GPU/audio resources before the frame loop starts."""
        self._container = pyav.open(str(self.video_path))
        if not self._container.streams.video:
            raise RuntimeError(f"no video stream found in {self.video_path}")

        self._video_stream = self._container.streams.video[0]
        self.width = int(self._video_stream.width)
        self.height = int(self._video_stream.height)
        average_rate = self._video_stream.average_rate
        if average_rate is not None and float(average_rate) > 0.0:
            self.fps = float(average_rate)
        self.frame_duration = 1.0 / self.fps
        self._row_bytes = self.width * 4
        self._pixel_count = self._row_bytes * self.height
        self._frames = iter(self._container.decode(video=0))

        self.source.width = self.width
        self.source.height = self.height
        self._fit_destination()
        self.video_label = f"Video: {self.width}x{self.height} @ {self.fps:.2f} fps"

        # A probe reveals whether PyAV pads RGBA rows for this resolution. The
        # fallback buffer is allocated once here, never inside the frame loop.
        probe = pyav.VideoFrame(self.width, self.height, "rgba")
        probe_plane = probe.planes[0]
        if probe_plane.line_size != self._row_bytes:
            self._tight_buffer = bytearray(self._pixel_count)
            self._tight_view = memoryview(self._tight_buffer)

        if not renderer.is_streaming_available() and not renderer.init_streaming():
            raise RuntimeError("OpenGL PBO streaming is unavailable")
        if not renderer.is_streaming_available():
            raise RuntimeError("OpenGL PBO streaming failed to initialize")

        self._streaming = renderer.create_streaming_texture(
            self.width, self.height, 4
        )
        if self._streaming is None:
            raise RuntimeError("could not create the PBO streaming texture")
        self._texture = renderer.get_streaming_texture(self._streaming)

        self._load_audio(audio)

        # PBO streaming is double buffered. Uploading the first decoded frame
        # twice primes both buffers before RENDER ever runs.
        first_pixels = self._decode_pixels(audio)
        if first_pixels is None:
            raise RuntimeError("the video contains no decodable frames")
        first_upload = renderer.update_streaming_texture(
            self._streaming, first_pixels
        )
        second_upload = renderer.update_streaming_texture(
            self._streaming, first_pixels
        )
        if not first_upload or not second_upload:
            raise RuntimeError("could not prime the PBO streaming texture")

    def _fit_destination(self) -> None:
        video_aspect = self.width / self.height
        window_aspect = WINDOW_WIDTH / WINDOW_HEIGHT
        if video_aspect > window_aspect:
            destination_width = WINDOW_WIDTH
            destination_height = int(WINDOW_WIDTH / video_aspect)
        else:
            destination_height = WINDOW_HEIGHT
            destination_width = int(WINDOW_HEIGHT * video_aspect)
        self.destination.x = (WINDOW_WIDTH - destination_width) // 2
        self.destination.y = (WINDOW_HEIGHT - destination_height) // 2
        self.destination.width = destination_width
        self.destination.height = destination_height

    def _load_audio(self, audio: AudioDevice) -> None:
        if self.audio_path is None:
            self.audio_label = "Audio: none (use --audio for a sidecar)"
            return
        loaded_music: ArepyMusic | None = None
        try:
            loaded_music = audio.load_music(self.audio_path)
            self._audio_length = audio.get_music_time_length(loaded_music)
            self._music = loaded_music
            self.audio_label = f"Audio: {self.audio_path.name}"
        except Exception as exc:
            if loaded_music is not None:
                try:
                    audio.unload_music(loaded_music)
                except Exception as unload_exc:
                    print(
                        f"Warning: could not unload failed sidecar: {unload_exc}",
                        file=sys.stderr,
                    )
            self._music = None
            self._audio_length = 0.0
            self.audio_label = "Audio: sidecar could not be loaded"
            print(f"Warning: could not load sidecar audio: {exc}", file=sys.stderr)

    def start(self, audio: AudioDevice) -> None:
        if self._music is not None:
            audio.play_music(self._music)
            self._audio_started = True

    def _rewind(self, audio: AudioDevice) -> bool:
        if not self.loop or self._container is None or self._video_stream is None:
            self._finished = True
            self.status_label = "Playback finished"
            if self._music is not None and self._audio_started:
                audio.stop_music(self._music)
                self._audio_started = False
            return False
        self._container.seek(
            0, backward=True, any_frame=False, stream=self._video_stream
        )
        self._frames = iter(self._container.decode(video=0))
        if self._music is not None:
            audio.seek_music_stream(self._music, 0.0)
        return True

    def _decode_pixels(self, audio: AudioDevice) -> memoryview | None:
        if self._frames is None:
            return None
        try:
            decoded_frame = next(self._frames)
        except StopIteration:
            if not self._rewind(audio):
                return None
            try:
                decoded_frame = next(self._frames)
            except StopIteration:
                self._finished = True
                self.status_label = "Playback finished: no frames after seek"
                return None

        if self._frame_view is not None:
            self._frame_view.release()
            self._frame_view = None
        self._rgba_frame = decoded_frame.reformat(format="rgba")
        plane = self._rgba_frame.planes[0]
        source_view = memoryview(plane)

        if plane.line_size == self._row_bytes and len(source_view) == self._pixel_count:
            self._frame_view = source_view
            return source_view

        # Padding is uncommon for standard video widths. Copy rows into the
        # reusable tight buffer created during initialize(); no per-frame pixel
        # container is allocated on this path either.
        destination = self._tight_view
        if destination is None:
            source_view.release()
            raise RuntimeError("PyAV returned an unexpected padded RGBA layout")
        source_offset = 0
        destination_offset = 0
        rows_remaining = self.height
        while rows_remaining > 0:
            destination[destination_offset : destination_offset + self._row_bytes] = (
                source_view[source_offset : source_offset + self._row_bytes]
            )
            source_offset += plane.line_size
            destination_offset += self._row_bytes
            rows_remaining -= 1
        source_view.release()
        return destination

    def update(self, renderer: Renderer2D, audio: AudioDevice) -> None:
        if self._music is not None:
            audio.update_music_stream(self._music)

        delta_time = renderer.get_delta_time()
        self.frame_accumulator += delta_time
        self.hud_accumulator += delta_time

        due_frames = int(self.frame_accumulator / self.frame_duration)
        if due_frames > MAX_DECODE_STEPS:
            due_frames = MAX_DECODE_STEPS
            self.frame_accumulator = 0.0
        elif due_frames > 0:
            self.frame_accumulator -= due_frames * self.frame_duration

        latest_pixels: memoryview | None = None
        while due_frames > 0:
            candidate = self._decode_pixels(audio)
            if candidate is None:
                break
            latest_pixels = candidate
            due_frames -= 1

        if latest_pixels is not None and self._streaming is not None:
            if not renderer.update_streaming_texture(self._streaming, latest_pixels):
                self.status_label = "Frame upload failed"

        if self.hud_accumulator >= HUD_REFRESH_SECONDS:
            self.hud_accumulator %= HUD_REFRESH_SECONDS
            self.fps_label = f"Window: {renderer.get_framerate()} FPS"
            if self._music is not None:
                played = audio.get_music_time_played(self._music)
                total = self._audio_length
                self.audio_label = f"Audio: {played:.1f}s / {total:.1f}s"
                progress = played / total if total > 0.0 else 0.0
                progress = min(1.0, max(0.0, progress))
                self.progress_fill.width = int(self.progress_track.width * progress)

    def render(self, renderer: Renderer2D) -> None:
        renderer.start_frame()
        renderer.clear(BLACK)
        if self._texture is None:
            renderer.draw_text(
                "Video texture unavailable", VIDEO_TEXT_POSITION, 20, RED
            )
        else:
            renderer.draw_texture_ex(
                self._texture,
                self.source,
                self.destination,
                VIDEO_ORIGIN,
                0.0,
                WHITE,
            )
            renderer.draw_text(self.video_label, VIDEO_TEXT_POSITION, 16, WHITE)
            renderer.draw_text(self.fps_label, FPS_TEXT_POSITION, 16, WHITE)
            renderer.draw_text(
                "PBO streaming: double buffered", STREAMING_TEXT_POSITION, 16, WHITE
            )
            renderer.draw_text(self.audio_label, AUDIO_TEXT_POSITION, 16, WHITE)
            if self._music is not None:
                renderer.draw_rectangle(self.progress_track, GRAY)
                renderer.draw_rectangle(self.progress_fill, WHITE)
            if self.status_label:
                renderer.draw_text(self.status_label, STATUS_TEXT_POSITION, 16, GRAY)
        renderer.end_frame()

    def close(self, renderer: Renderer2D, audio: AudioDevice) -> None:
        """Attempt every cleanup step; safe to call after partial initialization."""
        if self._closed:
            return
        self._closed = True

        if self._music is not None:
            try:
                if self._audio_started:
                    audio.stop_music(self._music)
            except Exception as exc:
                print(f"Warning: could not stop sidecar audio: {exc}", file=sys.stderr)
            try:
                audio.unload_music(self._music)
            except Exception as exc:
                print(
                    f"Warning: could not unload sidecar audio: {exc}",
                    file=sys.stderr,
                )
            self._music = None

        if self._frame_view is not None:
            self._frame_view.release()
            self._frame_view = None
        self._rgba_frame = None
        if self._tight_view is not None:
            self._tight_view.release()
            self._tight_view = None
        self._tight_buffer = None

        if self._streaming is not None:
            try:
                renderer.destroy_streaming_texture(self._streaming)
            except Exception as exc:
                print(
                    f"Warning: could not destroy streaming texture: {exc}",
                    file=sys.stderr,
                )
            self._streaming = None
            self._texture = None

        self._frames = None
        if self._container is not None:
            try:
                self._container.close()
            except Exception as exc:
                print(
                    f"Warning: could not close video container: {exc}",
                    file=sys.stderr,
                )
            self._container = None
            self._video_stream = None


def update_video(
    player: VideoPlayer, renderer: Renderer2D, audio: AudioDevice
) -> None:
    player.update(renderer, audio)


def render_video(player: VideoPlayer, renderer: Renderer2D) -> None:
    player.render(renderer)


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    try:
        pyav = _load_pyav()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    engine = ArepyEngine(
        title="Arepy video streaming",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        max_frame_rate=0,
        window_flags=WindowFlag.VSYNC_HINT,
    )
    player = VideoPlayer(config)
    try:
        player.initialize(pyav, engine.renderer_2d, engine.audio_device)
        engine.add_resource(player)

        world: World = engine.create_world("video")
        world.add_system(SystemPipeline.UPDATE, update_video)
        world.add_system(SystemPipeline.RENDER, render_video)
        engine.set_current_world("video")

        print(player.video_label)
        print(f"Audio sidecar: {config.audio_path or 'none'}")
        player.start(engine.audio_device)
        engine.run()
        return 0
    except Exception as exc:
        print(f"Video demo failed: {exc}", file=sys.stderr)
        return 1
    finally:
        player.close(engine.renderer_2d, engine.audio_device)


if __name__ == "__main__":
    raise SystemExit(main())
