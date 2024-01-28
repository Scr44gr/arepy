from typing import Dict

from arepy.ecs.registry import Entity


class CollisionEventHandler:
    """A class that stores the collision handler function and the entities that it handles"""

    def __init__(self):
        self.current_collisions: Dict[Entity, Entity] = {}

    def drop_collision(self, entity: Entity):
        """Remove the entity from the current collisions"""
        if entity in self.current_collisions:
            self.current_collisions.pop(entity)

    def add_collision(self, entity_a: Entity, entity_b: Entity):
        """Add the collision to the current collisions"""
        self.current_collisions[entity_a] = entity_b
        self.current_collisions[entity_b] = entity_a

    def is_colliding(self, entity: Entity) -> bool:
        """Return True if the entity is colliding with another entity"""
        return entity in self.current_collisions

    def get_colliding_entity(self, entity: Entity) -> Entity:
        """Return the entity that the entity is colliding with"""
        return self.current_collisions[entity]
