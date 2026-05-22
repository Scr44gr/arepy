import math
import random

from arepy_ecs import Component, Entity, Query, With, World

from arepy import ArepyEngine, Color, Input, Renderer2D, Renderer3D, SystemPipeline
from arepy.bundle.components.camera import Camera3D
from arepy.bundle.components.rigidbody import RigidBody3D
from arepy.bundle.components.transform import Transform3D
from arepy.math import Vec3

WHITE_COLOR = Color(255, 255, 255, 255)
RED_COLOR = Color(255, 0, 0, 255)
GREEN_COLOR = Color(0, 255, 0, 255)
BLUE_COLOR = Color(0, 0, 255, 255)
YELLOW_COLOR = Color(255, 255, 0, 255)
MAGENTA_COLOR = Color(255, 0, 255, 255)
CYAN_COLOR = Color(0, 255, 255, 255)

CUBE_COLORS = [
    RED_COLOR,
    GREEN_COLOR,
    BLUE_COLOR,
    YELLOW_COLOR,
    MAGENTA_COLOR,
    CYAN_COLOR,
]

CUBE_COUNT = 3000
WORLD_SIZE = 50.0
CUBE_SIZE = 1.0

# Pre-calculate constants to avoid repeated calculations
HALF_WORLD = WORLD_SIZE / 2
HALF_CUBE = CUBE_SIZE / 2
WORLD_BOUNDS_MIN = -HALF_WORLD + HALF_CUBE
WORLD_BOUNDS_MAX = HALF_WORLD - HALF_CUBE

# Pre-calculate grid parameters
GRID_SLICES = 20
GRID_SPACING = 5.0


class CachedInput(Component):
    """Component to cache input state for camera movement"""

    horizontal_angle: float = 0.0
    vertical_angle: float = 0.0
    distance: float = 20.0
    needs_update: bool = True
    smoothing_factor: float = 0.5
    target_horizontal: float = 0.0
    target_vertical: float = 0.0
    target_distance: float = 50.0
    center_threshold: int = 100
    mouse_was_centered: bool = False


def movement_system_3d(
    query: Query[Entity, With[Transform3D, RigidBody3D]], renderer: Renderer3D
) -> None:
    """3D movement system with bouncing physics - optimized version"""
    delta_time: float = renderer.get_delta_time()

    for transform, rigidbody in query.iter_components(Transform3D, RigidBody3D):
        transform.position_x += rigidbody.velocity_x * delta_time
        transform.position_y += rigidbody.velocity_y * delta_time
        transform.position_z += rigidbody.velocity_z * delta_time

        if transform.position_x <= WORLD_BOUNDS_MIN:
            transform.position_x = WORLD_BOUNDS_MIN
            rigidbody.velocity_x = abs(rigidbody.velocity_x)
        elif transform.position_x >= WORLD_BOUNDS_MAX:
            transform.position_x = WORLD_BOUNDS_MAX
            rigidbody.velocity_x = -abs(rigidbody.velocity_x)

        if transform.position_y <= WORLD_BOUNDS_MIN:
            transform.position_y = WORLD_BOUNDS_MIN
            rigidbody.velocity_y = abs(rigidbody.velocity_y)
        elif transform.position_y >= WORLD_BOUNDS_MAX:
            transform.position_y = WORLD_BOUNDS_MAX
            rigidbody.velocity_y = -abs(rigidbody.velocity_y)

        if transform.position_z <= WORLD_BOUNDS_MIN:
            transform.position_z = WORLD_BOUNDS_MIN
            rigidbody.velocity_z = abs(rigidbody.velocity_z)
        elif transform.position_z >= WORLD_BOUNDS_MAX:
            transform.position_z = WORLD_BOUNDS_MAX
            rigidbody.velocity_z = -abs(rigidbody.velocity_z)

        transform.rotation_x += rigidbody.angular_velocity_x * delta_time
        transform.rotation_y += rigidbody.angular_velocity_y * delta_time
        transform.rotation_z += rigidbody.angular_velocity_z * delta_time


def camera_system_3d(
    camera_query: Query[Entity, With[Camera3D, CachedInput]],
    renderer_3d: Renderer3D,
    input_device: Input,
    game: ArepyEngine,
) -> None:
    """Smooth camera system with smart mouse centering"""
    camera_components = next(
        camera_query.iter_components(Camera3D, CachedInput),
        None,
    )
    if camera_components is None:
        return

    camera, cached_input = camera_components

    # Get current mouse position and calculate center
    center_x = game.window_width // 2
    center_y = game.window_height // 2
    mouse_pos = input_device.get_mouse_position()

    # Calculate actual mouse delta, ignoring the frame where we just centered
    if cached_input.mouse_was_centered:
        mouse_delta = (0.0, 0.0)
        cached_input.mouse_was_centered = False
    else:
        mouse_delta = input_device.get_mouse_delta()

    wheel_delta = input_device.get_mouse_wheel_delta()

    mouse_sensitivity = 0.002  # Reduced sensitivity for smoother movement
    zoom_sensitivity = 1.5  # Reduced zoom sensitivity
    smoothing = cached_input.smoothing_factor

    # Initialize angles if first time
    if cached_input.needs_update:
        # Calculate initial spherical coordinates
        dx = camera.position_x - camera.target_x
        dy = camera.position_y - camera.target_y
        dz = camera.position_z - camera.target_z
        cached_input.distance = math.hypot(dx, dy, dz)
        cached_input.horizontal_angle = math.atan2(dx, dz)
        cos_vertical = max(-1.0, min(1.0, dy / cached_input.distance))
        cached_input.vertical_angle = math.acos(cos_vertical)

        cached_input.target_horizontal = cached_input.horizontal_angle
        cached_input.target_vertical = cached_input.vertical_angle
        cached_input.target_distance = cached_input.distance
        cached_input.needs_update = False

    # Update target angles based on mouse input
    if mouse_delta != (0.0, 0.0):
        cached_input.target_horizontal -= mouse_delta[0] * mouse_sensitivity
        cached_input.target_vertical += mouse_delta[1] * mouse_sensitivity
        cached_input.target_vertical = max(
            0.1, min(math.pi - 0.1, cached_input.target_vertical)
        )

    # Update target distance based on wheel input
    if wheel_delta != 0.0:
        cached_input.target_distance -= wheel_delta * zoom_sensitivity
        cached_input.target_distance = max(
            2.0, min(100.0, cached_input.target_distance)
        )

    # Smooth interpolation towards target values
    cached_input.horizontal_angle += (
        cached_input.target_horizontal - cached_input.horizontal_angle
    ) * smoothing
    cached_input.vertical_angle += (
        cached_input.target_vertical - cached_input.vertical_angle
    ) * smoothing
    cached_input.distance += (
        cached_input.target_distance - cached_input.distance
    ) * smoothing

    # Pre-calculate trigonometric values
    sin_vertical = math.sin(cached_input.vertical_angle)
    cos_vertical = math.cos(cached_input.vertical_angle)
    sin_horizontal = math.sin(cached_input.horizontal_angle)
    cos_horizontal = math.cos(cached_input.horizontal_angle)

    # Update camera position using smoothed values
    camera.position_x = (
        camera.target_x + cached_input.distance * sin_vertical * sin_horizontal
    )
    camera.position_y = camera.target_y + cached_input.distance * cos_vertical
    camera.position_z = (
        camera.target_z + cached_input.distance * sin_vertical * cos_horizontal
    )

    # Smart mouse recentering - only when mouse gets too far from center
    distance_from_center = math.hypot(mouse_pos[0] - center_x, mouse_pos[1] - center_y)

    if distance_from_center > cached_input.center_threshold:
        game.renderer_2d.set_mouse_position((center_x, center_y))
        cached_input.mouse_was_centered = True
    renderer_3d.update_camera(camera)


def render_system_3d(
    query: Query[Entity, With[Transform3D]],
    camera_query: Query[Entity, With[Camera3D]],
    renderer: Renderer3D,
    renderer_2d: Renderer2D,
) -> None:
    """Optimized 3D rendering system"""
    # Start 2D frame
    renderer_2d.start_frame()
    renderer_2d.clear(color=Color(30, 30, 50, 255))

    # Get camera
    camera = next(camera_query.iter_components(Camera3D), None)
    if camera is None:
        renderer_2d.end_frame()
        return

    camera = camera[0]

    # Begin 3D mode
    renderer.begin_mode_3d(camera)

    # Draw world boundaries (wireframe cube) - using pre-calculated values
    renderer.draw_cube_wires(
        Vec3(0.0, 0.0, 0.0),
        WORLD_SIZE,
        WORLD_SIZE,
        WORLD_SIZE,
        Color(100, 100, 100, 255),
    )

    # Draw grid using pre-calculated values
    renderer.draw_grid(GRID_SLICES, GRID_SPACING)

    # Pre-calculate color count to avoid modulo in tight loop
    color_count = len(CUBE_COLORS)
    number_of_entities: int = 0

    # Optimized rendering loop - minimize object creation
    for (transform,) in query.iter_components(Transform3D):

        # Use fast color cycling
        color = CUBE_COLORS[number_of_entities % color_count]

        renderer.draw_cube(
            Vec3(transform.position_x, transform.position_y, transform.position_z),
            transform.scale_x,
            transform.scale_y,
            transform.scale_z,
            color,
        )

        number_of_entities += 1

    # End 3D mode
    renderer.end_mode_3d()

    # Draw 2D UI overlay
    renderer_2d.draw_text(
        f"3D Cubes: {number_of_entities}",
        (10, 30),
        font_size=20,
        color=WHITE_COLOR,
    )

    renderer_2d.draw_text(
        "Mouse: rotate | Wheel: zoom | Smart centering",
        (10, 60),
        font_size=16,
        color=Color(200, 200, 200, 255),
    )

    renderer_2d.draw_fps((10, 10))
    renderer_2d.end_frame()


def spawn_cubes_3d(world: World, count: int) -> None:
    """Spawn 3D cubes with random positions, velocities, and rotations - optimized"""
    # Pre-calculate bounds to avoid repeated calculations
    spawn_bound = HALF_WORLD - CUBE_SIZE

    for _ in range(count):
        # Random position within world bounds
        x: float = random.uniform(-spawn_bound, spawn_bound)
        y: float = random.uniform(-spawn_bound, spawn_bound)
        z: float = random.uniform(-spawn_bound, spawn_bound)

        # Random velocity
        vx: float = random.uniform(-15.0, 15.0)
        vy: float = random.uniform(-15.0, 15.0)
        vz: float = random.uniform(-15.0, 15.0)

        # Random angular velocity for rotation
        avx: float = random.uniform(-90.0, 90.0)  # degrees per second
        avy: float = random.uniform(-90.0, 90.0)
        avz: float = random.uniform(-90.0, 90.0)

        world.create_entity().with_component(
            Transform3D(
                position_x=x,
                position_y=y,
                position_z=z,
                scale_x=CUBE_SIZE,
                scale_y=CUBE_SIZE,
                scale_z=CUBE_SIZE,
            )
        ).with_component(
            RigidBody3D(
                velocity_x=vx,
                velocity_y=vy,
                velocity_z=vz,
                angular_velocity_x=avx,
                angular_velocity_y=avy,
                angular_velocity_z=avz,
            )
        ).build()


def main() -> None:
    game: ArepyEngine = ArepyEngine(
        title="Arepy CubeMark 3D",
        width=1024,
        height=768,
        max_frame_rate=0,
    )

    world: World = game.create_world("cubemark_3d")

    # Create 3D camera with cached input
    cached_input = CachedInput(
        needs_update=True,
        target_distance=34.64,
        distance=34.64,
    )

    _ = (  # as camera entity
        world.create_entity()
        .with_component(
            Camera3D(
                position_x=20.0,
                position_y=20.0,
                position_z=20.0,
                target_x=0.0,
                target_y=0.0,
                target_z=0.0,
                up_x=0.0,
                up_y=1.0,
                up_z=0.0,
                fovy=45.0,
                projection=0,  # PERSPECTIVE
            )
        )
        .with_component(cached_input)
        .build()
    )

    # Spawn 3D cubes
    spawn_cubes_3d(world, CUBE_COUNT)
    # set mouse cursor to center
    game.renderer_2d.disable_mouse_cursor()

    # Register systems
    world.add_system(SystemPipeline.UPDATE, movement_system_3d)
    world.add_system(SystemPipeline.UPDATE, camera_system_3d)
    world.add_system(SystemPipeline.RENDER, render_system_3d)

    game.set_current_world("cubemark_3d")
    game.run()


if __name__ == "__main__":
    main()
