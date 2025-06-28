import math
import random

from arepy import ArepyEngine, Color, Input, Renderer2D, Renderer3D, SystemPipeline
from arepy.bundle.components.camera import Camera3D
from arepy.bundle.components.rigidbody import RigidBody3D
from arepy.bundle.components.transform import Transform3D
from arepy.ecs import Entities, Query, With
from arepy.ecs.components import Component
from arepy.ecs.world import World
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

CUBE_COUNT = 10
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

    def __init__(self):
        self.mouse_delta = (0.0, 0.0)  # Mouse delta for rotation
        self.wheel_delta = 0.0  # Mouse wheel delta for zoom
        self.horizontal_angle = 0.0  # Cached horizontal angle
        self.vertical_angle = 0.0  # Cached vertical angle
        self.distance = 20.0  # Cached camera distance
        self.needs_update = True  # Flag to avoid unnecessary calculations
        self.smoothing_factor = 0.5  # For smooth camera movement
        self.target_horizontal = 0.0  # Target angle for smooth interpolation
        self.target_vertical = 0.0  # Target angle for smooth interpolation
        self.target_distance = 50.0  # Target distance for smooth zoom
        self.center_threshold = 100  # Distance from center before recentering
        self.mouse_was_centered = False  # Track if we just centered the mouse


def movement_system_3d(
    query: Query[Entities, With[Transform3D, RigidBody3D]], renderer: Renderer3D
) -> None:
    """3D movement system with bouncing physics - optimized version"""
    delta_time: float = renderer.get_delta_time()

    for entity in query.get_entities():
        transform = entity.get_component(Transform3D)
        rigidbody = entity.get_component(RigidBody3D)

        pos = transform.position
        vel = rigidbody.velocity
        rot = transform.rotation
        ang_vel = rigidbody.angular_velocity

        pos.x += vel.x * delta_time
        pos.y += vel.y * delta_time
        pos.z += vel.z * delta_time

        if pos.x <= WORLD_BOUNDS_MIN:
            pos.x = WORLD_BOUNDS_MIN
            vel.x = abs(vel.x)
        elif pos.x >= WORLD_BOUNDS_MAX:
            pos.x = WORLD_BOUNDS_MAX
            vel.x = -abs(vel.x)

        if pos.y <= WORLD_BOUNDS_MIN:
            pos.y = WORLD_BOUNDS_MIN
            vel.y = abs(vel.y)
        elif pos.y >= WORLD_BOUNDS_MAX:
            pos.y = WORLD_BOUNDS_MAX
            vel.y = -abs(vel.y)

        if pos.z <= WORLD_BOUNDS_MIN:
            pos.z = WORLD_BOUNDS_MIN
            vel.z = abs(vel.z)
        elif pos.z >= WORLD_BOUNDS_MAX:
            pos.z = WORLD_BOUNDS_MAX
            vel.z = -abs(vel.z)

        rot.x += ang_vel.x * delta_time
        rot.y += ang_vel.y * delta_time
        rot.z += ang_vel.z * delta_time


def camera_system_3d(
    camera_query: Query[Entities, With[Camera3D]],
    renderer_3d: Renderer3D,
    input_device: Input,
    game: ArepyEngine,
) -> None:
    """Smooth camera system with smart mouse centering"""
    camera_entities = list(camera_query.get_entities())
    if not camera_entities:
        return

    camera_entity = camera_entities[0]
    camera = camera_entity.get_component(Camera3D)
    cached_input = camera_entity.get_component(CachedInput)

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
        distance_vec = Vec3(
            camera.position.x - camera.target.x,
            camera.position.y - camera.target.y,
            camera.position.z - camera.target.z,
        )
        cached_input.distance = math.sqrt(
            distance_vec.x**2 + distance_vec.y**2 + distance_vec.z**2
        )
        cached_input.horizontal_angle = math.atan2(distance_vec.x, distance_vec.z)
        cos_vertical = max(-1.0, min(1.0, distance_vec.y / cached_input.distance))
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
    camera.position.x = (
        camera.target.x + cached_input.distance * sin_vertical * sin_horizontal
    )
    camera.position.y = camera.target.y + cached_input.distance * cos_vertical
    camera.position.z = (
        camera.target.z + cached_input.distance * sin_vertical * cos_horizontal
    )

    # Smart mouse recentering - only when mouse gets too far from center
    distance_from_center = math.sqrt(
        (mouse_pos[0] - center_x) ** 2 + (mouse_pos[1] - center_y) ** 2
    )

    if distance_from_center > cached_input.center_threshold:
        game.renderer.set_mouse_position((center_x, center_y))
        cached_input.mouse_was_centered = True
    renderer_3d.update_camera(camera)
    # Cache input state for next frame
    cached_input.mouse_delta = mouse_delta
    cached_input.wheel_delta = wheel_delta


def render_system_3d(
    query: Query[Entities, With[Transform3D]],
    camera_query: Query[Entities, With[Camera3D]],
    renderer: Renderer3D,
    renderer_2d: Renderer2D,
    game: ArepyEngine,
) -> None:
    """Optimized 3D rendering system"""
    # Start 2D frame
    renderer_2d.start_frame()
    renderer_2d.clear(color=Color(30, 30, 50, 255))

    # Get camera
    camera_entities = list(camera_query.get_entities())
    if not camera_entities:
        renderer_2d.end_frame()
        return

    camera = camera_entities[0].get_component(Camera3D)

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
    for entity in query.get_entities():
        transform = entity.get_component(Transform3D)

        # Use fast color cycling
        color = CUBE_COLORS[number_of_entities % color_count]

        # Direct position access, reuse Vec3 creation
        pos = transform.position
        scale = transform.scale

        renderer.draw_cube(
            Vec3(pos.x, pos.y, pos.z),
            scale.x,
            scale.y,
            scale.z,
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
                position=Vec3(x, y, z),
                rotation=Vec3(0.0, 0.0, 0.0),
                scale=Vec3(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE),
            )
        ).with_component(
            RigidBody3D(
                velocity=Vec3(vx, vy, vz),
                acceleration=Vec3(0.0, 0.0, 0.0),
                angular_velocity=Vec3(avx, avy, avz),
            )
        ).build()


def main() -> None:
    game: ArepyEngine = ArepyEngine()
    game.title = "Arepy CubeMark 3D"
    game.window_width = 1024
    game.window_height = 768
    game.max_frame_rate = 0  # Unlimited
    game.init()

    world: World = game.create_world("cubemark_3d")

    # Create 3D camera with cached input
    cached_input = CachedInput()
    cached_input.needs_update = True  # Force initial calculation
    cached_input.target_distance = 34.64  # sqrt(20^2 + 20^2 + 20^2) / sqrt(3)
    cached_input.distance = cached_input.target_distance

    _ = (  # as camera entity
        world.create_entity()
        .with_component(
            Camera3D(
                position=Vec3(20.0, 20.0, 20.0),
                target=Vec3(0.0, 0.0, 0.0),
                up=Vec3(0.0, 1.0, 0.0),
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
    game.renderer.disable_mouse_cursor()

    # Register systems
    world.add_system(SystemPipeline.UPDATE, movement_system_3d)
    world.add_system(SystemPipeline.UPDATE, camera_system_3d)
    world.add_system(SystemPipeline.RENDER, render_system_3d)

    game.set_current_world("cubemark_3d")
    game.run()


if __name__ == "__main__":
    main()
