"""Builder-specific exceptions."""


class BuilderError(RuntimeError):
    """Base error raised for invalid or failed game builds."""


class ConfigurationError(BuilderError):
    """Raised when a build configuration is invalid."""


class ToolUnavailableError(BuilderError):
    """Raised when a target's external compiler is unavailable."""
