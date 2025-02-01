from typing import Set

from .builders import EntityBuilder
from .registry import Registry
from .systems import System, SystemPipeline, SystemState


class World:

    def __init__(self, name: str):
        self._registry = Registry()
        self.name = name

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
        self._registry.add_system(pipeline, SystemState.ON, system)

    def add_systems(self, pipeline: SystemPipeline, systems: Set[System]) -> None:
        """Create multiple systems.

        Args:
            pipeline: A pipeline to add the system.
            systems: A list of systems.
        """
        for system in systems:
            self.add_system(pipeline, system)

    def add_system_with_state(
        self, pipeline: SystemPipeline, system: System, state: SystemState
    ) -> None:
        """Create a new system with a state.

        Args:
            pipeline: A pipeline to add the system.
            system: A system.
            state: A state.
        """
        self._registry.add_system(pipeline, state, system)

    def set_system_state(
        self, pipeline: SystemPipeline, system: System, state: SystemState
    ) -> None:
        """Set the state of a system.

        Args:
            pipeline: The pipeline of the system.
            system: A system.
            state: A state.
        """
        self._registry.set_system_state(pipeline, system, state)

    def get_registry(self) -> Registry:
        """Get ECS the registry.

        Returns:
            The registry.
        """
        return self._registry
