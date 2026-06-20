"""Explicit 3D API surface for the initial web backend."""


def load_model(path: object) -> object:
    _unsupported("load_model")


def load_model_from_mesh(mesh: object) -> object:
    _unsupported("load_model_from_mesh")


def unload_model(model: object) -> None:
    _unsupported("unload_model")


def generate_mesh_plane(
    width: float,
    length: float,
    res_x: int,
    res_z: int,
) -> object:
    _unsupported("generate_mesh_plane")


def generate_mesh_cube(width: float, height: float, length: float) -> object:
    _unsupported("generate_mesh_cube")


def generate_mesh_sphere(radius: float, rings: int, slices: int) -> object:
    _unsupported("generate_mesh_sphere")


def unload_mesh(mesh: object) -> None:
    _unsupported("unload_mesh")


def get_delta_time() -> float:
    _unsupported("get_delta_time")


def create_material() -> object:
    _unsupported("create_material")


def load_material_default() -> object:
    _unsupported("load_material_default")


def unload_material(material: object) -> None:
    _unsupported("unload_material")


def draw_model(
    model: object,
    position: object,
    scale: float,
    tint: object,
) -> None:
    _unsupported("draw_model")


def draw_model_ex(
    model: object,
    position: object,
    rotation_axis: object,
    rotation_angle: float,
    scale: object,
    tint: object,
) -> None:
    _unsupported("draw_model_ex")


def draw_model_wires(
    model: object,
    position: object,
    scale: float,
    tint: object,
) -> None:
    _unsupported("draw_model_wires")


def draw_cube(
    position: object,
    width: float,
    height: float,
    length: float,
    color: object,
) -> None:
    _unsupported("draw_cube")


def draw_cube_v(position: object, size: object, color: object) -> None:
    _unsupported("draw_cube_v")


def draw_cube_wires(
    position: object,
    width: float,
    height: float,
    length: float,
    color: object,
) -> None:
    _unsupported("draw_cube_wires")


def draw_sphere(center_pos: object, radius: float, color: object) -> None:
    _unsupported("draw_sphere")


def draw_sphere_ex(
    center_pos: object,
    radius: float,
    rings: int,
    slices: int,
    color: object,
) -> None:
    _unsupported("draw_sphere_ex")


def draw_sphere_wires(
    center_pos: object,
    radius: float,
    rings: int,
    slices: int,
    color: object,
) -> None:
    _unsupported("draw_sphere_wires")


def draw_plane(center_pos: object, size: object, color: object) -> None:
    _unsupported("draw_plane")


def draw_billboard(
    texture: object,
    position: object,
    size: float,
    tint: object,
) -> None:
    _unsupported("draw_billboard")


def draw_billboard_rec(
    texture: object,
    source: object,
    position: object,
    size: object,
    tint: object,
) -> None:
    _unsupported("draw_billboard_rec")


def draw_grid(slices: int, spacing: float) -> None:
    _unsupported("draw_grid")


def add_camera(camera: object) -> None:
    _unsupported("add_camera")


def get_camera(id: int) -> object:
    _unsupported("get_camera")


def remove_camera(id: int) -> None:
    _unsupported("remove_camera")


def begin_mode_3d(camera: object) -> None:
    _unsupported("begin_mode_3d")


def end_mode_3d() -> None:
    _unsupported("end_mode_3d")


def update_camera(camera: object, mode: int = 0) -> None:
    _unsupported("update_camera")


def get_cameras() -> list[object]:
    _unsupported("get_cameras")


def get_current_camera() -> object:
    _unsupported("get_current_camera")


def set_lighting_enabled(enabled: bool) -> None:
    _unsupported("set_lighting_enabled")


def get_ray_collision_mesh(ray: object, mesh: object, transform: object) -> object:
    _unsupported("get_ray_collision_mesh")


def get_ray_collision_triangle(
    ray: object,
    p1: object,
    p2: object,
    p3: object,
) -> object:
    _unsupported("get_ray_collision_triangle")


def _unsupported(operation: str) -> None:
    raise NotImplementedError(
        f"Renderer3D.{operation} is not available in the current Arepy web backend."
    )
