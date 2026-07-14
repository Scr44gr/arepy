"""Target registry and build orchestration."""

from collections.abc import Iterable

from .config import BuildConfig
from .errors import ConfigurationError
from .models import BuildArtifact, BuildTarget
from .targets import WebTarget, WindowsTarget
from .targets.base import TargetBuilder


class Builder:
    """Extensible orchestrator for Arepy platform exporters."""

    def __init__(self, targets: Iterable[TargetBuilder] | None = None) -> None:
        implementations = (
            (WindowsTarget(), WebTarget()) if targets is None else targets
        )
        self._targets = {
            implementation.target: implementation
            for implementation in implementations
        }

    def register(self, target: TargetBuilder) -> None:
        """Register or replace a platform target implementation."""

        self._targets[target.target] = target

    def build(
        self,
        config: BuildConfig,
        targets: Iterable[BuildTarget | str],
    ) -> list[BuildArtifact]:
        """Build the requested targets in order."""

        config.validate()
        artifacts: list[BuildArtifact] = []
        for raw_target in targets:
            try:
                target = (
                    raw_target
                    if isinstance(raw_target, BuildTarget)
                    else BuildTarget(raw_target)
                )
            except ValueError as error:
                raise ConfigurationError(
                    f"Unsupported build target: {raw_target}"
                ) from error
            implementation = self._targets.get(target)
            if implementation is None:
                raise ConfigurationError(
                    f"No builder implementation is registered for '{target.value}'."
                )
            artifacts.append(implementation.build(config))
        return artifacts
