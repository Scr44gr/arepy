"""Shared, target-independent builder models."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class BuildTarget(str, Enum):
    """Platforms supported by the built-in target registry."""

    WINDOWS = "windows"
    WEB = "web"


@dataclass(frozen=True, slots=True)
class BuildArtifact:
    """A completed target build and its update manifest."""

    target: BuildTarget
    output_path: Path
    manifest_path: Path
