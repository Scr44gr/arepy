"""Target extension point."""

from typing import Protocol

from ..config import BuildConfig
from ..models import BuildArtifact, BuildTarget


class TargetBuilder(Protocol):
    """Contract implemented by platform-specific exporters."""

    target: BuildTarget

    def build(self, config: BuildConfig) -> BuildArtifact:
        """Build one target and return its primary artifact."""
        ...
