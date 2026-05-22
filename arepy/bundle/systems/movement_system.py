from arepy_ecs import Entities, Query, With

from arepy.bundle.components import RigidBody2D, Transform
from arepy.engine.renderer.renderer_2d import Renderer2D

LIMITS = (640 - 32, 480 - 32)


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]],
    renderer: Renderer2D,
):
    delta_time = renderer.get_delta_time()
    for transform, rigidbody in query.iter_components(Transform, RigidBody2D):
        transform.position_x += rigidbody.velocity_x * delta_time
        transform.position_y += rigidbody.velocity_y * delta_time

        if transform.position_x < 0:
            transform.position_x = 0
            rigidbody.velocity_x = -rigidbody.velocity_x

        if transform.position_y < 0:
            transform.position_y = 0
            rigidbody.velocity_y = -rigidbody.velocity_y

        if transform.position_x > LIMITS[0]:
            transform.position_x = LIMITS[0]
            rigidbody.velocity_x = -rigidbody.velocity_x

        if transform.position_y > LIMITS[1]:
            transform.position_y = LIMITS[1]
            rigidbody.velocity_y = -rigidbody.velocity_y
