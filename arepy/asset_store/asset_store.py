from dataclasses import dataclass, field
from enum import Enum
from os.path import exists
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from ..engine.audio import ArepyMusic, ArepySound, AudioDevice
from ..engine.renderer import ArepyTexture
from ..engine.renderer.renderer_2d import Renderer2D

if TYPE_CHECKING:
    from ..engine.renderer.renderer_3d import (
        ArepyMaterial,
        ArepyMesh,
        ArepyModel,
        Renderer3D,
    )


class TextureFilter(Enum):
    NEAREST = 0
    LINEAR = 1


@dataclass(frozen=True, slots=True)
class AssetStore:
    textures: Dict[str, ArepyTexture] = field(default_factory=dict)
    fonts: Dict[str, Any] = field(default_factory=dict)
    sounds: Dict[str, ArepySound] = field(default_factory=dict)
    musics: Dict[str, ArepyMusic] = field(default_factory=dict)
    # 3D assets
    models: Dict[str, "ArepyModel"] = field(default_factory=dict)
    meshes: Dict[str, "ArepyMesh"] = field(default_factory=dict)
    materials: Dict[str, "ArepyMaterial"] = field(default_factory=dict)

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

    # 3D Asset methods
    def load_model(self, renderer: "Renderer3D", name: str, path: str) -> None:
        """Load a 3D model from file."""
        if not exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")

        self.models[name] = renderer.load_model(Path(path))

    def create_mesh_cube(
        self,
        renderer: "Renderer3D",
        name: str,
        width: float,
        height: float,
        length: float,
    ) -> None:
        """Create a cube mesh."""
        self.meshes[name] = renderer.generate_mesh_cube(width, height, length)

    def create_mesh_sphere(
        self,
        renderer: "Renderer3D",
        name: str,
        radius: float,
        rings: int = 16,
        slices: int = 16,
    ) -> None:
        """Create a sphere mesh."""
        self.meshes[name] = renderer.generate_mesh_sphere(radius, rings, slices)

    def create_mesh_plane(
        self,
        renderer: "Renderer3D",
        name: str,
        width: float,
        length: float,
        res_x: int = 1,
        res_z: int = 1,
    ) -> None:
        """Create a plane mesh."""
        self.meshes[name] = renderer.generate_mesh_plane(width, length, res_x, res_z)

    def create_material(self, renderer: "Renderer3D", name: str) -> None:
        """Create a new material."""
        self.materials[name] = renderer.create_material()

    def load_material_default(self, renderer: "Renderer3D", name: str) -> None:
        """Load the default material."""
        self.materials[name] = renderer.load_material_default()

    def get_model(self, name: str) -> "ArepyModel":
        """Get a model by name."""
        return self.models[name]

    def get_mesh(self, name: str) -> "ArepyMesh":
        """Get a mesh by name."""
        return self.meshes[name]

    def get_material(self, name: str) -> "ArepyMaterial":
        """Get a material by name."""
        return self.materials[name]

    def unload_model(self, renderer: "Renderer3D", name: str) -> None:
        """Unload a model."""
        model = self.models.pop(name)
        renderer.unload_model(model)

    def unload_mesh(self, renderer: "Renderer3D", name: str) -> None:
        """Unload a mesh."""
        mesh = self.meshes.pop(name)
        renderer.unload_mesh(mesh)

    def unload_material(self, renderer: "Renderer3D", name: str) -> None:
        """Unload a material."""
        material = self.materials.pop(name)
        renderer.unload_material(material)
