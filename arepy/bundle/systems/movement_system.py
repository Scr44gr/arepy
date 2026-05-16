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
        position = transform.position
        velocity = rigidbody.velocity

        position.x += velocity.x * delta_time
        position.y += velocity.y * delta_time

        if position.x < 0:
            position.x = 0
            velocity.x = -velocity.x

        if position.y < 0:
            position.y = 0
            velocity.y = -velocity.y

        if position.x > LIMITS[0]:
            position.x = LIMITS[0]
            velocity.x = -velocity.x

        if position.y > LIMITS[1]:
            position.y = LIMITS[1]
            velocity.y = -velocity.y
