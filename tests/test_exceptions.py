import pytest

from arepy.ecs.components import Component
from arepy.ecs.exceptions import (
    ComponentNotFoundError,
    MaximumComponentsExceededError,
    RegistryNotSetError,
)


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


class TestExceptions:
    def test_component_not_found_error(self):
        """Test ComponentNotFoundError exception."""
        with pytest.raises(ComponentNotFoundError) as exc_info:
            raise ComponentNotFoundError(Position)

        exception = exc_info.value

        # Test string representation
        error_str = str(exception)
        assert "Position" in error_str
        assert "not" in error_str.lower() or "does" in error_str.lower()

    def test_component_not_found_error_message(self):
        """Test ComponentNotFoundError message format."""
        error = ComponentNotFoundError(Position)
        message = str(error)

        # Should contain component type name
        assert "Position" in message
        # Should be informative
        assert len(message) > 10

    def test_registry_not_set_error(self):
        """Test RegistryNotSetError exception."""
        with pytest.raises(RegistryNotSetError) as exc_info:
            raise RegistryNotSetError()

        exception = exc_info.value

        # Test that exception can be raised and caught
        assert isinstance(exception, RegistryNotSetError)
        assert isinstance(exception, Exception)

    def test_registry_not_set_error_message(self):
        """Test RegistryNotSetError message format."""
        error = RegistryNotSetError()
        message = str(error)

        # Should be a string (even if empty)
        assert isinstance(message, str)

    def test_exception_inheritance(self):
        """Test that custom exceptions inherit from appropriate base classes."""
        component_error = ComponentNotFoundError(Position)
        registry_error = RegistryNotSetError()

        # Should be instances of Exception
        assert isinstance(component_error, Exception)
        assert isinstance(registry_error, Exception)

    def test_component_not_found_error_with_different_types(self):
        """Test ComponentNotFoundError with different component types."""

        class Velocity(Component):
            pass

        class Health(Component):
            pass

        # Test with different component types
        pos_error = ComponentNotFoundError(Position)
        vel_error = ComponentNotFoundError(Velocity)
        health_error = ComponentNotFoundError(Health)

        # Messages should contain the component type names
        assert "Position" in str(pos_error)
        assert "Velocity" in str(vel_error)
        assert "Health" in str(health_error)

        # Messages should be different
        assert str(pos_error) != str(vel_error)
        assert str(vel_error) != str(health_error)

    def test_exception_can_be_caught(self):
        """Test that exceptions can be properly caught."""
        # Test ComponentNotFoundError
        try:
            raise ComponentNotFoundError(Position)
        except ComponentNotFoundError as e:
            assert "Position" in str(e)
        else:
            pytest.fail("ComponentNotFoundError was not raised")

        # Test RegistryNotSetError
        try:
            raise RegistryNotSetError()
        except RegistryNotSetError:
            pass  # Expected
        else:
            pytest.fail("RegistryNotSetError was not raised")

    def test_exception_reraise(self):
        """Test that exceptions can be re-raised properly."""

        def inner_function():
            raise ComponentNotFoundError(Position)

        def outer_function():
            try:
                inner_function()
            except ComponentNotFoundError:
                raise  # Re-raise the same exception

        with pytest.raises(ComponentNotFoundError) as exc_info:
            outer_function()

        assert "Position" in str(exc_info.value)

    def test_maximum_components_exceeded_error(self):
        """Test MaximumComponentsExceededError exception."""
        max_components = 1024

        with pytest.raises(MaximumComponentsExceededError) as exc_info:
            raise MaximumComponentsExceededError(max_components)

        exception = exc_info.value
        error_str = str(exception)

        # Should contain the max components number
        assert str(max_components) in error_str
        assert "maximum" in error_str.lower() or "exceeded" in error_str.lower()

    def test_maximum_components_exceeded_error_message_format(self):
        """Test MaximumComponentsExceededError message format with different values."""
        test_values = [100, 512, 1024, 2048]

        for max_val in test_values:
            error = MaximumComponentsExceededError(max_val)
            message = str(error)

            # Should contain the specific number
            assert str(max_val) in message
            # Should be informative
            assert len(message) > 10
