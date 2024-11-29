from ...ecs.systems import System
from ..components.rigidbody_component import RigidBody2D
from ..components.transform_component import Transform

LIMITS = (800, 600)


class MovementSystem(System):

    def __init__(self) -> None:
        super().__init__()
        self.require_components([Transform, RigidBody2D])

    def update(self, delta_time: float):

        for entity in self.get_entities():
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
