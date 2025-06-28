from os import PathLike
from typing import Any, List, Optional, cast

import raylib as rl
from pyray import Camera3D as rlCamera3D
from pyray import Vector2 as rlVector2
from pyray import Vector3 as rlVec3

from arepy.bundle.components.camera import Camera3D
from arepy.engine.renderer import Color
from arepy.engine.renderer.renderer_3d import ArepyMaterial, ArepyMesh, ArepyModel
from arepy.math.vec2 import Vec2
from arepy.math.vec3 import Vec3

# Global camera management
_cameras: List[Camera3D] = []
_current_camera: Optional[Camera3D] = None


def load_model(path: PathLike[str]) -> ArepyModel:
    """
    Load a 3D model from a file.

    Args:
        path: Path to the model file

    Returns:
        ArepyModel: The loaded model
    """
    model = rl.LoadModel(str(path).encode("utf-8"))
    arepy_model = ArepyModel(
        model.meshCount,
        model.meshes[0].vertexCount if model.meshCount > 0 else 0,
        model.meshes[0].triangleCount if model.meshCount > 0 else 0,
    )
    arepy_model._ref_model = model
    return arepy_model


def load_model_from_mesh(mesh: ArepyMesh) -> ArepyModel:
    """
    Load a model from a mesh.

    Args:
        mesh: The mesh to create the model from

    Returns:
        ArepyModel: The created model
    """
    model = rl.LoadModelFromMesh(cast(Any, mesh._ref_mesh))
    arepy_model = ArepyModel(1, mesh.vertex_count, mesh.triangle_count)
    arepy_model._ref_model = model
    return arepy_model


def unload_model(model: ArepyModel) -> None:
    """
    Unload a 3D model.

    Args:
        model: The model to unload
    """
    rl.UnloadModel(cast(Any, model._ref_model))


def generate_mesh_plane(
    width: float, length: float, res_x: int, res_z: int
) -> ArepyMesh:
    """
    Generate a plane mesh.

    Args:
        width: Width of the plane
        length: Length of the plane
        res_x: Resolution on X axis
        res_z: Resolution on Z axis

    Returns:
        ArepyMesh: The generated mesh
    """
    mesh = rl.GenMeshPlane(width, length, res_x, res_z)
    arepy_mesh = ArepyMesh(0, mesh.vertexCount, mesh.triangleCount)
    arepy_mesh._ref_mesh = mesh
    return arepy_mesh


def generate_mesh_cube(width: float, height: float, length: float) -> ArepyMesh:
    """
    Generate a cube mesh.

    Args:
        width: Width of the cube
        height: Height of the cube
        length: Length of the cube

    Returns:
        ArepyMesh: The generated mesh
    """
    mesh = rl.GenMeshCube(width, height, length)
    arepy_mesh = ArepyMesh(0, mesh.vertexCount, mesh.triangleCount)
    arepy_mesh._ref_mesh = mesh
    return arepy_mesh


def generate_mesh_sphere(radius: float, rings: int, slices: int) -> ArepyMesh:
    """
    Generate a sphere mesh.

    Args:
        radius: Radius of the sphere
        rings: Number of rings
        slices: Number of slices

    Returns:
        ArepyMesh: The generated mesh
    """
    mesh = rl.GenMeshSphere(radius, rings, slices)
    arepy_mesh = ArepyMesh(0, mesh.vertexCount, mesh.triangleCount)
    arepy_mesh._ref_mesh = mesh
    return arepy_mesh


def unload_mesh(mesh: ArepyMesh) -> None:
    """
    Unload a mesh.

    Args:
        mesh: The mesh to unload
    """
    rl.UnloadMesh(cast(Any, mesh._ref_mesh))


def create_material() -> ArepyMaterial:
    """
    Create a new material.

    Returns:
        ArepyMaterial: The created material
    """
    material = rl.LoadMaterialDefault()
    arepy_material = ArepyMaterial(0)
    arepy_material._ref_material = material
    return arepy_material


def load_material_default() -> ArepyMaterial:
    """
    Load the default material.

    Returns:
        ArepyMaterial: The default material
    """
    material = rl.LoadMaterialDefault()
    arepy_material = ArepyMaterial(0)
    arepy_material._ref_material = material
    return arepy_material


def unload_material(material: ArepyMaterial) -> None:
    """
    Unload a material.

    Args:
        material: The material to unload
    """
    rl.UnloadMaterial(cast(Any, material._ref_material))


def draw_model(model: ArepyModel, position: Vec3, scale: float, tint: Color) -> None:
    """
    Draw a 3D model.

    Args:
        model: The model to draw
        position: Position to draw at
        scale: Scale factor
        tint: Color tint
    """
    rl.DrawModel(
        cast(Any, model._ref_model),
        position.to_tuple(),
        scale,
        (tint.r, tint.g, tint.b, tint.a),
    )


def draw_model_ex(
    model: ArepyModel,
    position: Vec3,
    rotation_axis: Vec3,
    rotation_angle: float,
    scale: Vec3,
    tint: Color,
) -> None:
    """
    Draw a 3D model with extended parameters.

    Args:
        model: The model to draw
        position: Position to draw at
        rotation_axis: Axis of rotation
        rotation_angle: Rotation angle in degrees
        scale: Scale vector
        tint: Color tint
    """
    rl.DrawModelEx(
        cast(Any, model._ref_model),
        position.to_tuple(),
        rotation_axis.to_tuple(),
        rotation_angle,
        scale.to_tuple(),
        (tint.r, tint.g, tint.b, tint.a),
    )


def draw_model_wires(
    model: ArepyModel, position: Vec3, scale: float, tint: Color
) -> None:
    """
    Draw a 3D model in wireframe mode.

    Args:
        model: The model to draw
        position: Position to draw at
        scale: Scale factor
        tint: Color tint
    """
    rl.DrawModelWires(
        cast(Any, model._ref_model),
        position.to_tuple(),
        scale,
        (tint.r, tint.g, tint.b, tint.a),
    )


def draw_cube(
    position: Vec3, width: float, height: float, length: float, color: Color
) -> None:
    """
    Draw a cube.

    Args:
        position: Position to draw at
        width: Width of the cube
        height: Height of the cube
        length: Length of the cube
        color: Color of the cube
    """
    rl.DrawCube(
        position.to_tuple(), width, height, length, (color.r, color.g, color.b, color.a)
    )


def draw_cube_v(position: Vec3, size: Vec3, color: Color) -> None:
    """
    Draw a cube with vector size.

    Args:
        position: Position to draw at
        size: Size vector (width, height, length)
        color: Color of the cube
    """
    rl.DrawCubeV(
        position.to_tuple(), size.to_tuple(), (color.r, color.g, color.b, color.a)
    )


def draw_cube_wires(
    position: Vec3, width: float, height: float, length: float, color: Color
) -> None:
    """
    Draw a cube in wireframe mode.

    Args:
        position: Position to draw at
        width: Width of the cube
        height: Height of the cube
        length: Length of the cube
        color: Color of the cube
    """
    rl.DrawCubeWires(
        position.to_tuple(), width, height, length, (color.r, color.g, color.b, color.a)
    )


def draw_sphere(center_pos: Vec3, radius: float, color: Color) -> None:
    """
    Draw a sphere.

    Args:
        center_pos: Center position of the sphere
        radius: Radius of the sphere
        color: Color of the sphere
    """
    rl.DrawSphere(center_pos.to_tuple(), radius, (color.r, color.g, color.b, color.a))


def draw_sphere_ex(
    center_pos: Vec3, radius: float, rings: int, slices: int, color: Color
) -> None:
    """
    Draw a sphere with extended parameters.

    Args:
        center_pos: Center position of the sphere
        radius: Radius of the sphere
        rings: Number of rings
        slices: Number of slices
        color: Color of the sphere
    """
    rl.DrawSphereEx(
        center_pos.to_tuple(),
        radius,
        rings,
        slices,
        (color.r, color.g, color.b, color.a),
    )


def draw_sphere_wires(
    center_pos: Vec3, radius: float, rings: int, slices: int, color: Color
) -> None:
    """
    Draw a sphere in wireframe mode.

    Args:
        center_pos: Center position of the sphere
        radius: Radius of the sphere
        rings: Number of rings
        slices: Number of slices
        color: Color of the sphere
    """
    rl.DrawSphereWires(
        center_pos.to_tuple(),
        radius,
        rings,
        slices,
        (color.r, color.g, color.b, color.a),
    )


def draw_plane(center_pos: Vec3, size: Vec2, color: Color) -> None:
    """
    Draw a plane.

    Args:
        center_pos: Center position of the plane
        size: Size of the plane (width, length)
        color: Color of the plane
    """
    rl.DrawPlane(
        center_pos.to_tuple(), size.to_tuple(), (color.r, color.g, color.b, color.a)
    )


def draw_grid(slices: int, spacing: float) -> None:
    """
    Draw a grid.

    Args:
        slices: Number of slices
        spacing: Spacing between grid lines
    """
    rl.DrawGrid(slices, spacing)


def add_camera(camera: Camera3D) -> None:
    """
    Add a 3D camera and initialize its internal reference.

    Args:
        camera: The 3D camera to add
    """
    global _cameras, _current_camera

    if camera._ref is None:
        rl_camera = rlCamera3D()
        rl_camera.position = rlVec3(
            camera.position.x, camera.position.y, camera.position.z
        )
        rl_camera.target = rlVec3(camera.target.x, camera.target.y, camera.target.z)
        rl_camera.up = rlVec3(camera.up.x, camera.up.y, camera.up.z)
        rl_camera.fovy = camera.fovy
        rl_camera.projection = camera.projection
        camera._ref = cast(Any, rl_camera)

    # Add to cameras list if not already present
    if camera not in _cameras:
        _cameras.append(camera)

    # Set as current camera if it's the first one
    if _current_camera is None:
        _current_camera = camera


def get_camera(id: int) -> Optional[Camera3D]:
    """
    Get a camera by index.

    Args:
        id: Index of the camera

    Returns:
        Camera3D or None if not found
    """
    global _cameras
    if 0 <= id < len(_cameras):
        return _cameras[id]
    return None


def remove_camera(id: int) -> None:
    """
    Remove a camera by index.

    Args:
        id: Index of the camera to remove
    """
    global _cameras, _current_camera
    if 0 <= id < len(_cameras):
        camera_to_remove = _cameras[id]
        _cameras.pop(id)

        # If removing current camera, set new current camera
        if _current_camera == camera_to_remove:
            _current_camera = _cameras[0] if _cameras else None


def begin_mode_3d(camera: Camera3D) -> None:
    """
    Begin 3D mode with camera.

    Args:
        camera: The 3D camera to use
    """
    global _current_camera

    # Ensure camera has been added (has _ref)
    if camera._ref is None:
        add_camera(camera)

    # Set as current camera
    _current_camera = camera

    rl.BeginMode3D(cast(Any, camera._ref))


def end_mode_3d() -> None:
    """
    End 3D mode.
    """
    rl.EndMode3D()


def update_camera(camera: Camera3D, mode: int = 0) -> None:
    """
    Update camera position and target.

    Args:
        camera: The camera to update
        mode: Camera mode (0=CUSTOM, 1=FREE, 2=ORBITAL, etc.) - currently unused
    """
    if camera._ref is not None:
        rl_camera = cast(rlCamera3D, camera._ref)

        # Update the raylib camera with current arepy camera values
        rl_camera.position.x = camera.position.x
        rl_camera.position.y = camera.position.y
        rl_camera.position.z = camera.position.z
        rl_camera.target.x = camera.target.x
        rl_camera.target.y = camera.target.y
        rl_camera.target.z = camera.target.z
        rl_camera.up.x = camera.up.x
        rl_camera.up.y = camera.up.y
        rl_camera.up.z = camera.up.z
        rl_camera.fovy = camera.fovy
        rl_camera.projection = camera.projection


def set_lighting_enabled(enabled: bool) -> None:
    """
    Enable or disable lighting (placeholder for more advanced lighting system).

    Args:
        enabled: Whether to enable lighting
    """
    # This is a placeholder - Raylib handles lighting through shaders
    # For basic usage, default material should handle basic lighting
    pass


def get_ray_collision_mesh(ray: Any, mesh: ArepyMesh, transform: Any) -> Any:
    """
    Get ray collision with mesh.

    Args:
        ray: The ray to test
        mesh: The mesh to test against
        transform: Transform matrix

    Returns:
        Collision information
    """
    return rl.GetRayCollisionMesh(ray, cast(Any, mesh._ref_mesh), transform)


def get_ray_collision_triangle(ray: Any, p1: Vec3, p2: Vec3, p3: Vec3) -> Any:
    """
    Get ray collision with triangle.

    Args:
        ray: The ray to test
        p1: First triangle vertex
        p2: Second triangle vertex
        p3: Third triangle vertex

    Returns:
        Collision information
    """
    return rl.GetRayCollisionTriangle(ray, p1.to_tuple(), p2.to_tuple(), p3.to_tuple())


def get_delta_time() -> float:
    """
    Get the time elapsed since the last frame.

    Returns:
        Time in seconds
    """
    return rl.GetFrameTime()


# Camera management functions
def get_cameras() -> List[Camera3D]:
    """
    Get list of all cameras.

    Returns:
        List of Camera3D objects
    """
    global _cameras
    return _cameras


def get_current_camera() -> Camera3D:
    """
    Get the current active camera.

    Returns:
        Current Camera3D object

    Raises:
        RuntimeError: If no camera is set
    """
    global _current_camera
    if _current_camera is None:
        raise RuntimeError("No current camera set")
    return _current_camera
