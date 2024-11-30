from ...ecs.query import EntityWith, Query
from ...engine.renderer.renderer_2d import Renderer2D
from ..components.rigidbody_component import RigidBody2D
from ..components.transform_component import Transform

LIMITS = (800, 600)


def movement_system(
    query: Query[EntityWith[Transform, RigidBody2D]], renderer: Renderer2D
):
    delta_time = renderer.get_delta_time()

    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        velocity = entity.get_component(RigidBody2D).velocity
        transform.position += velocity * delta_time

        if transform.position.x < 0:
            transform.position.x = 0
            velocity.x *= -1
        if transform.position.y < 0:
            transform.position.y = 0
            velocity.y *= -1

        if transform.position.x > LIMITS[0]:
            transform.position.x = LIMITS[0]
            velocity.x *= -1
        if transform.position.y > LIMITS[1]:
            transform.position.y = LIMITS[1]
            velocity.y *= -1
