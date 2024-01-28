import logging

from arepy.ecs.systems import System

from ..components import Rigidbody, Transform


class MovementSystem(System):
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()
        self.require_component(Transform)
        self.require_component(Rigidbody)

    def update(self, delta_time: float):
        self.logger.info("Updating MovementSystem")

        for entity in self.get_system_entities():
            transform = entity.get_component(Transform)
            velocity = entity.get_component(Rigidbody).velocity

            transform.position.x += velocity.x * delta_time
            transform.position.y += velocity.y * delta_time
