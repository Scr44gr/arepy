from typing import Type

from .components import TComponent


class RegistryNotSetError(Exception):
    """Raised when the registry is not set."""


class MaximumComponentsExceededError(Exception):
    """Raised when the maximum number of components is exceeded."""

    def __init__(self, max_components: int) -> None:
        super().__init__(f"Maximum number of components ({max_components}) exceeded.")


class ComponentNotFoundError(Exception):
    """Raised when a component is not found."""

    def __init__(self, component_type: Type[TComponent]) -> None:
        super().__init__(f"Component {component_type} does not exist.")
