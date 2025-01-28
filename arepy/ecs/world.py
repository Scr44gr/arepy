from .builders import EntityBuilder
from .registry import Registry
from .systems import System, SystemPipeline


class World:

    def __init__(self):
        self._registry = Registry()

    def create_entity(self):
        """Create an entity builder.

        Returns:
            An entity builder.
        """
        entity = self._registry.create_entity()
        return EntityBuilder(entity, self._registry)

    def add_system(self, pipeline: SystemPipeline, system: System) -> None:
        """Create a new system.

        Args:
            pipeline: A pipeline to add the system.
            system: A system.
        """
        registry = self._registry
        registry.add_system(pipeline, system)

    def get_registry(self) -> Registry:
        """Get ECS the registry.

        Returns:
            The registry.
        """
        return self._registry
