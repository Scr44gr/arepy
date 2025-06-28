from os import PathLike
from typing import Any, Optional, Protocol, Tuple

from arepy.bundle.components.camera import Camera3D
from arepy.math.vec2 import Vec2
from arepy.math.vec3 import Vec3

from . import ArepyTexture, Color


class ArepyModel:
    """Wrapper for 3D models in Arepy engine."""

    def __init__(self, model_id: int, vertex_count: int, triangle_count: int):
        self.model_id = model_id
        self.vertex_count = vertex_count
        self.triangle_count = triangle_count
        self._ref_model: object = None

    def unload(self) -> None:
        """Unload the model from memory."""
        ...


class ArepyMesh:
    """Wrapper for 3D meshes in Arepy engine."""

    def __init__(self, mesh_id: int, vertex_count: int, triangle_count: int):
        self.mesh_id = mesh_id
        self.vertex_count = vertex_count
        self.triangle_count = triangle_count
        self._ref_mesh: object = None


class ArepyMaterial:
    """Wrapper for 3D materials in Arepy engine."""

    def __init__(self, material_id: int):
        self.material_id = material_id
        self._ref_material: object = None

    def set_texture(self, texture: ArepyTexture, texture_type: int) -> None:
        """Set texture for specific material map type."""
        ...


class Renderer3D(Protocol):
    """Protocol defining the 3D renderer interface."""

    # Model methods
    def load_model(self, path: PathLike[str]) -> ArepyModel: ...
    def load_model_from_mesh(self, mesh: ArepyMesh) -> ArepyModel: ...
    def unload_model(self, model: ArepyModel) -> None: ...

    # Mesh methods
    def generate_mesh_plane(
        self, width: float, length: float, res_x: int, res_z: int
    ) -> ArepyMesh: ...
    def generate_mesh_cube(
        self, width: float, height: float, length: float
    ) -> ArepyMesh: ...
    def generate_mesh_sphere(
        self, radius: float, rings: int, slices: int
    ) -> ArepyMesh: ...
    def unload_mesh(self, mesh: ArepyMesh) -> None: ...
    def get_delta_time(self) -> float: ...

    # Material methods
    def create_material(self) -> ArepyMaterial: ...
    def load_material_default(self) -> ArepyMaterial: ...
    def unload_material(self, material: ArepyMaterial) -> None: ...

    # Drawing methods
    def draw_model(
        self, model: ArepyModel, position: Vec3, scale: float, tint: Color
    ) -> None: ...
    def draw_model_ex(
        self,
        model: ArepyModel,
        position: Vec3,
        rotation_axis: Vec3,
        rotation_angle: float,
        scale: Vec3,
        tint: Color,
    ) -> None: ...
    def draw_model_wires(
        self, model: ArepyModel, position: Vec3, scale: float, tint: Color
    ) -> None: ...

    # Primitive drawing methods
    def draw_cube(
        self,
        position: Vec3,
        width: float,
        height: float,
        length: float,
        color: Color,
    ) -> None: ...
    def draw_cube_v(self, position: Vec3, size: Vec3, color: Color) -> None: ...
    def draw_cube_wires(
        self,
        position: Vec3,
        width: float,
        height: float,
        length: float,
        color: Color,
    ) -> None: ...
    def draw_sphere(self, center_pos: Vec3, radius: float, color: Color) -> None: ...
    def draw_sphere_ex(
        self, center_pos: Vec3, radius: float, rings: int, slices: int, color: Color
    ) -> None: ...
    def draw_sphere_wires(
        self, center_pos: Vec3, radius: float, rings: int, slices: int, color: Color
    ) -> None: ...
    def draw_plane(self, center_pos: Vec3, size: Vec2, color: Color) -> None: ...
    def draw_grid(self, slices: int, spacing: float) -> None: ...

    # Camera methods
    def add_camera(self, camera: Camera3D) -> None: ...
    def get_camera(self, id: int) -> Optional[Camera3D]: ...
    def remove_camera(self, id: int) -> None: ...
    def begin_mode_3d(self, camera: Camera3D) -> None: ...
    def end_mode_3d(self) -> None: ...
    def update_camera(self, camera: Camera3D, mode: int = 0) -> None: ...
    def get_cameras(self) -> list[Camera3D]: ...
    def get_current_camera(self) -> Camera3D: ...

    # Lighting methods (basic support)
    def set_lighting_enabled(self, enabled: bool) -> None: ...

    # Utility methods
    def get_ray_collision_mesh(
        self, ray: Any, mesh: ArepyMesh, transform: Any
    ) -> Any: ...
    def get_ray_collision_triangle(
        self, ray: Any, p1: Vec3, p2: Vec3, p3: Vec3
    ) -> Any: ...
