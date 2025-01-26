from dataclasses import dataclass, field
from enum import Enum
from os.path import exists
from pathlib import Path
from typing import Any, Dict

from ..engine.audio import ArepyMusic, ArepySound, AudioDevice
from ..engine.renderer import ArepyTexture
from ..engine.renderer.renderer_2d import Renderer2D


class TextureFilter(Enum):
    NEAREST = 0
    LINEAR = 1


@dataclass(frozen=True, slots=True)
class AssetStore:
    textures: Dict[str, ArepyTexture] = field(default_factory=dict)
    fonts: Dict[str, Any] = field(default_factory=dict)
    sounds: Dict[str, ArepySound] = field(default_factory=dict)
    musics: Dict[str, ArepyMusic] = field(default_factory=dict)

    def create_render_texture(
        self,
        renderer: Renderer2D,
        name: str,
        width: int,
        height: int,
    ) -> ArepyTexture:
        texture = renderer.create_render_texture(width, height)
        self.textures[name] = texture
        return texture

    def load_texture(
        self,
        renderer: Renderer2D,
        name: str,
        path: str,
    ) -> None:
        if not exists(path):
            raise FileNotFoundError(f"Texture file not found: {path}")

        self.textures[name] = renderer.create_texture(path=Path(path))

    def load_font(self, name: str, path: str, size: int) -> None: ...
    def get_texture(self, name: str) -> ArepyTexture:
        return self.textures[name]

    def get_font(self, name: str) -> Any:
        return self.fonts[name]

    def unload_texture(self, renderer: Renderer2D, name: str) -> None:

        texture = self.textures.pop(name)
        renderer.unload_texture(texture)

    # Audio related methods
    def load_sound(self, audio_device: AudioDevice, name: str, path: str):
        sound = audio_device.load_sound(Path(path))
        self.sounds[name] = sound

    def load_music(self, audio_device: AudioDevice, name: str, path: str):
        music = audio_device.load_music(Path(path))
        self.musics[name] = music

    def get_sound(self, name: str) -> ArepySound:
        return self.sounds[name]

    def get_music(self, name: str) -> ArepyMusic:
        return self.musics[name]

    def unload_sound(self, audio_device: AudioDevice, name: str):
        sound = self.sounds.pop(name)
        audio_device.unload_sound(sound)

    def unload_music(self, audio_device: AudioDevice, name: str):
        music = self.musics.pop(name)
        audio_device.unload_music(music)
