"""Configuration loading for Arepy game builds."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class BuildConfig:
    """Normalized configuration consumed by every build target."""

    project_root: Path
    entrypoint: Path
    name: str
    version: str = "0.1.0"
    output_dir: Path = Path("dist/arepy")
    assets: tuple[Path, ...] = field(default_factory=lambda: (Path("assets"),))
    icon: Path | None = None
    embed_assets: bool = False
    web_title: str | None = None
    pyodide_version: str = "314.0.0"

    @classmethod
    def from_file(cls, path: str | Path) -> "BuildConfig":
        """Load a configuration from an ``arepy.build.toml`` file."""

        config_path = Path(path).resolve()
        try:
            document = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ConfigurationError(
                f"Build configuration was not found: {config_path}"
            ) from error
        except tomllib.TOMLDecodeError as error:
            raise ConfigurationError(
                f"Invalid TOML in build configuration: {error}"
            ) from error

        raw = document.get("build", document)
        if not isinstance(raw, dict):
            raise ConfigurationError("The build configuration must be a TOML table.")
        return cls.from_mapping(raw, project_root=config_path.parent)

    @classmethod
    def from_mapping(
        cls,
        raw: dict[str, Any],
        *,
        project_root: str | Path,
    ) -> "BuildConfig":
        """Create a normalized configuration from a mapping."""

        root = Path(project_root).resolve()
        entry_value = raw.get("entrypoint")
        name_value = raw.get("name")
        if not isinstance(entry_value, str) or not entry_value:
            raise ConfigurationError("'entrypoint' must be a non-empty string.")
        if not isinstance(name_value, str) or not name_value:
            raise ConfigurationError("'name' must be a non-empty string.")

        assets_value = raw.get("assets", ["assets"])
        if not isinstance(assets_value, list) or not all(
            isinstance(item, str) for item in assets_value
        ):
            raise ConfigurationError("'assets' must be an array of paths.")

        config = cls(
            project_root=root,
            entrypoint=_resolve(root, entry_value),
            name=name_value,
            version=str(raw.get("version", "0.1.0")),
            output_dir=_resolve(root, str(raw.get("output_dir", "dist/arepy"))),
            assets=tuple(_resolve(root, item) for item in assets_value),
            icon=(
                _resolve(root, raw["icon"])
                if isinstance(raw.get("icon"), str)
                else None
            ),
            embed_assets=bool(raw.get("embed_assets", False)),
            web_title=(
                str(raw["web_title"]) if raw.get("web_title") is not None else None
            ),
            pyodide_version=str(raw.get("pyodide_version", "314.0.0")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate paths and values shared by all targets."""

        if not self.entrypoint.is_file():
            raise ConfigurationError(f"Entrypoint does not exist: {self.entrypoint}")
        if self.entrypoint.suffix != ".py":
            raise ConfigurationError("Entrypoint must be a Python file.")
        if not self.name.replace("-", "").replace("_", "").isalnum():
            raise ConfigurationError(
                "Build name may contain only letters, numbers, '-' and '_'."
            )
        missing_assets = [path for path in self.assets if not path.exists()]
        if missing_assets:
            joined = ", ".join(str(path) for path in missing_assets)
            raise ConfigurationError(f"Asset paths do not exist: {joined}")
        if self.icon is not None and not self.icon.is_file():
            raise ConfigurationError(f"Icon does not exist: {self.icon}")


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()
