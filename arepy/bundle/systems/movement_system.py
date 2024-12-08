from ...ecs.entities import Entities
from ...ecs.query import Query, With
from ...engine.renderer.renderer_2d import Renderer2D
from ..components.rigidbody_component import RigidBody2D
from ..components.transform_component import Transform

LIMITS = (640 - 32, 480 - 32)


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]], renderer: Renderer2D
):
    delta_time = renderer.get_delta_time()
    entities = query.get_entities()
    for entity in entities:
        transform = entity.get_component(Transform)
        velocity = entity.get_component(RigidBody2D).velocity

        transform.position.x += velocity.x * delta_time
        transform.position.y += velocity.y * delta_time

        if transform.position.x < 0:
            transform.position.x = 0
            velocity.x = -velocity.x

        if transform.position.y < 0:

            transform.position.y = 0
            velocity.y = -velocity.y

        if transform.position.x > LIMITS[0]:

            transform.position.x = LIMITS[0]
            velocity.x = -velocity.x

        if transform.position.y > LIMITS[1]:

            transform.position.y = LIMITS[1]
            velocity.y = -velocity.y
