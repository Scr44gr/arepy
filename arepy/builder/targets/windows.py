"""Nuitka-backed Windows exporter."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys

from ..assets import build_asset_pack
from ..config import BuildConfig
from ..errors import BuilderError, ToolUnavailableError
from ..manifest import write_release_manifest
from ..models import BuildArtifact, BuildTarget


class WindowsTarget:
    """Compile an Arepy game into a single Windows executable."""

    target = BuildTarget.WINDOWS

    def build(self, config: BuildConfig) -> BuildArtifact:
        """Build a Nuitka onefile executable and update manifest."""

        if sys.platform != "win32":
            raise ToolUnavailableError(
                "The Windows target must be built on Windows or a Windows CI runner."
            )
        if not _module_available("nuitka"):
            raise ToolUnavailableError(
                "Nuitka is unavailable. Install the builder extra: "
                "pip install 'arepy[builder]'"
            )

        target_dir = config.output_dir / "windows"
        work_dir = target_dir / ".work"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        legacy_pack = target_dir / f"{config.name}.arepy-assets"
        if legacy_pack.exists():
            legacy_pack.unlink()

        pack_path = (
            work_dir if config.embed_assets else target_dir
        ) / f"{config.name}.assets"
        pack = build_asset_pack(
            config.assets,
            pack_path,
            project_root=config.project_root,
        )
        module_name = _entry_module(config)
        bootstrap = work_dir / "_arepy_bootstrap.py"
        bootstrap.write_text(
            _bootstrap_source(
                module_name=module_name,
                pack_name=pack.path.name,
                encoded_key=pack.encoded_key,
                embedded=config.embed_assets,
            ),
            encoding="utf-8",
        )

        executable = target_dir / f"{config.name}.exe"
        command = [
            sys.executable,
            "-m",
            "nuitka",
            "--mode=onefile",
            "--assume-yes-for-downloads",
            "--remove-output",
            f"--output-dir={target_dir}",
            f"--output-filename={executable.name}",
            "--windows-console-mode=disable",
            f"--include-module={module_name}",
            "--include-module=arepy.arepy_renderer",
            "--include-package=cryptography",
            "--nofollow-import-to=imgui_bundle,OpenGL,zengl",
            "--nofollow-import-to=arepy.engine.integrations.imgui",
            "--nofollow-import-to=arepy.engine.integrations.web",
        ]
        if config.embed_assets:
            command.append(f"--include-data-files={pack.path}={pack.path.name}")
        if config.icon is not None:
            command.append(f"--windows-icon-from-ico={config.icon}")
        command.append(str(bootstrap))

        result = subprocess.run(
            command,
            cwd=config.project_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            diagnostics = (result.stdout + "\n" + result.stderr).strip()
            raise BuilderError(f"Nuitka build failed:\n{diagnostics[-8000:]}")
        if not executable.is_file():
            raise BuilderError(f"Nuitka did not produce the expected file: {executable}")

        release_files = [executable]
        if not config.embed_assets:
            release_files.append(pack.path)
        manifest = write_release_manifest(
            target_dir / "release.json",
            name=config.name,
            version=config.version,
            target=self.target.value,
            files=release_files,
        )
        shutil.rmtree(work_dir, ignore_errors=True)
        return BuildArtifact(self.target, executable, manifest)


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _entry_module(config: BuildConfig) -> str:
    try:
        relative = config.entrypoint.relative_to(config.project_root)
    except ValueError as error:
        raise BuilderError("Entrypoint must be inside project_root.") from error
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _bootstrap_source(
    *,
    module_name: str,
    pack_name: str,
    encoded_key: str,
    embedded: bool,
) -> str:
    pack_expression = (
        f"_bundle_dir / {pack_name!r}"
        if embedded
        else f"_application_dir / {pack_name!r}"
    )
    return f'''import os
import sys
import traceback
from pathlib import Path

_bundle_dir = Path(__file__).resolve().parent
_application_dir = Path(sys.argv[0]).resolve().parent
os.environ["AREPY_ASSET_PACK"] = str({pack_expression})
os.environ["AREPY_ASSET_KEY"] = {encoded_key!r}
os.environ["AREPY_DISABLE_IMGUI"] = "1"

if __name__ == "__main__":
    try:
        from {module_name} import main as _arepy_main
        _arepy_main()
    except BaseException:
        (_application_dir / "arepy-crash.log").write_text(
            traceback.format_exc(),
            encoding="utf-8",
        )
        raise
'''
