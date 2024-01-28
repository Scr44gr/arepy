from ...ecs.registry import Entity
from ..event_manager import Event


class CollisionEvent(Event):
    """Collision event"""

    def __init__(self, entity_a: Entity, entity_b: Entity):
        super().__init__()
        self.entity_a = entity_a
        self.entity_b = entity_b
