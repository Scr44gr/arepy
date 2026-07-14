"""Configuration loading for Arepy game builds."""

from __future__ import annotations

import keyword
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
    pyodide_version: str = "314.0.2"

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

        output_value = raw.get("output_dir", "dist/arepy")
        if not isinstance(output_value, str) or not output_value:
            raise ConfigurationError("'output_dir' must be a non-empty string.")
        icon_value = raw.get("icon")
        if icon_value is not None and not isinstance(icon_value, str):
            raise ConfigurationError("'icon' must be a path string when provided.")
        embed_assets_value = raw.get("embed_assets", False)
        if not isinstance(embed_assets_value, bool):
            raise ConfigurationError("'embed_assets' must be a boolean.")

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
            output_dir=_resolve(root, output_value),
            assets=tuple(_resolve(root, item) for item in assets_value),
            icon=_resolve(root, icon_value) if icon_value is not None else None,
            embed_assets=embed_assets_value,
            web_title=(
                str(raw["web_title"]) if raw.get("web_title") is not None else None
            ),
            pyodide_version=str(raw.get("pyodide_version", "314.0.2")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate paths and values shared by all targets."""

        project_root = self.project_root.resolve()
        if not project_root.is_dir():
            raise ConfigurationError(
                f"Project root does not exist or is not a directory: {project_root}"
            )
        if not self.entrypoint.is_file():
            raise ConfigurationError(f"Entrypoint does not exist: {self.entrypoint}")
        if self.entrypoint.suffix != ".py":
            raise ConfigurationError("Entrypoint must be a Python file.")
        _entry_module_name(self)
        if not isinstance(self.name, str) or not self.name.replace(
            "-", ""
        ).replace("_", "").isalnum():
            raise ConfigurationError(
                "Build name may contain only letters, numbers, '-' and '_'."
            )
        if not str(self.version).strip():
            raise ConfigurationError("Build version must not be empty.")
        if not isinstance(self.embed_assets, bool):
            raise ConfigurationError("'embed_assets' must be a boolean.")
        if not str(self.pyodide_version).strip():
            raise ConfigurationError("Pyodide version must not be empty.")
        if self.output_dir.exists() and not self.output_dir.is_dir():
            raise ConfigurationError(
                f"Output path exists and is not a directory: {self.output_dir}"
            )
        missing_assets = [path for path in self.assets if not path.exists()]
        if missing_assets:
            joined = ", ".join(str(path) for path in missing_assets)
            raise ConfigurationError(f"Asset paths do not exist: {joined}")
        output_dir = self.output_dir.resolve()
        for asset_root in self.assets:
            if asset_root.is_dir() and output_dir.is_relative_to(asset_root.resolve()):
                raise ConfigurationError(
                    "Output directory must not be inside an asset directory: "
                    f"{asset_root}"
                )
        if self.icon is not None and not self.icon.is_file():
            raise ConfigurationError(f"Icon does not exist: {self.icon}")


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _entry_module_name(config: BuildConfig) -> str:
    project_root = config.project_root.resolve()
    entrypoint = config.entrypoint.resolve()
    try:
        relative = entrypoint.relative_to(project_root)
    except ValueError as error:
        raise ConfigurationError("Entrypoint must be inside project_root.") from error

    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    invalid_parts = [
        part for part in parts if not part.isidentifier() or keyword.iskeyword(part)
    ]
    if not parts or invalid_parts:
        invalid = ", ".join(invalid_parts) or str(relative)
        raise ConfigurationError(
            f"Entrypoint path does not form a valid Python module: {invalid}"
        )
    return ".".join(parts)
