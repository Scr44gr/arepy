import json
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from arepy.builder import _staging as staging_module
from arepy.builder import assets as assets_module
from arepy.builder._staging import staged_output_directory
from arepy.builder.assets import AssetPack, build_asset_pack
from arepy.builder.cli import _unique_targets, create_parser
from arepy.builder.config import BuildConfig
from arepy.builder.core import Builder
from arepy.builder.errors import BuilderError, ConfigurationError
from arepy.builder.models import BuildArtifact, BuildTarget
from arepy.builder.targets import web as web_module
from arepy.builder.targets import windows as windows_module
from arepy.runtime_assets import resolve_asset_path


def test_cli_accepts_export_option() -> None:
    args = create_parser().parse_args(
        ["--export", "web", "--config", "game.build.toml"]
    )

    assert args.export_targets == ["web"]


def test_cli_keeps_legacy_targets_as_compatibility_alias() -> None:
    args = create_parser("arepy-build").parse_args(["windows", "web"])

    assert args.legacy_targets == ["windows", "web"]


def test_cli_removes_duplicate_targets_without_changing_order() -> None:
    targets = _unique_targets(["web", "windows", "web"])

    assert targets == ["web", "windows"]


def test_config_resolves_paths_relative_to_configuration(tmp_path: Path) -> None:
    entrypoint = tmp_path / "game.py"
    entrypoint.write_text("def main(): pass\n", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    config_file = tmp_path / "arepy.build.toml"
    config_file.write_text(
        '[build]\nentrypoint="game.py"\nname="game"\nassets=["assets"]\n',
        encoding="utf-8",
    )

    config = BuildConfig.from_file(config_file)

    assert config.entrypoint == entrypoint


def test_asset_pack_round_trip_resolves_original_logical_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assets = tmp_path / "nested" / "assets"
    assets.mkdir(parents=True)
    original = b"secret bunny"
    (assets / "bunny.png").write_bytes(original)
    monkeypatch.setattr(assets_module, "_PAYLOAD_SPOOL_LIMIT", 1)
    pack = build_asset_pack(
        (assets,),
        tmp_path / "game.assets",
        project_root=tmp_path,
    )
    monkeypatch.chdir(tmp_path / "nested")
    monkeypatch.setenv("AREPY_ASSET_PACK", str(pack.path))
    monkeypatch.setenv("AREPY_ASSET_KEY", pack.encoded_key)

    resolved = resolve_asset_path("./assets/bunny.png")

    assert resolved.read_bytes() == original


def test_asset_pack_does_not_include_its_previous_output(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "sprite.txt").write_text("asset", encoding="utf-8")
    output = assets / "game.assets"
    output.write_bytes(b"previous pack")

    pack = build_asset_pack((assets,), output, project_root=tmp_path)

    assert "assets/game.assets" not in pack.entries
    assert pack.entries == ("assets/sprite.txt",)


def test_builder_accepts_registered_target(tmp_path: Path) -> None:
    entrypoint = tmp_path / "game.py"
    entrypoint.write_text("def main(): pass\n", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    config = BuildConfig(
        project_root=tmp_path,
        entrypoint=entrypoint,
        name="game",
        output_dir=tmp_path / "dist",
        assets=(assets,),
    )

    class FakeTarget:
        target = BuildTarget.WEB

        def build(self, build_config: BuildConfig) -> BuildArtifact:
            output = build_config.output_dir / "index.html"
            output.parent.mkdir(parents=True)
            output.write_text("", encoding="utf-8")
            manifest = output.parent / "release.json"
            manifest.write_text(json.dumps({}), encoding="utf-8")
            return BuildArtifact(self.target, output, manifest)

    artifacts = Builder((FakeTarget(),)).build(config, ("web",))

    assert artifacts[0].target is BuildTarget.WEB


def test_builder_respects_explicit_empty_target_registry(tmp_path: Path) -> None:
    config = _target_config(tmp_path)

    with pytest.raises(ConfigurationError, match="No builder implementation"):
        Builder(()).build(config, ("web",))


def test_config_rejects_entrypoint_outside_project_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    assets = project_root / "assets"
    assets.mkdir()
    entrypoint = tmp_path / "outside.py"
    entrypoint.write_text("def main(): pass\n", encoding="utf-8")
    config = BuildConfig(
        project_root=project_root,
        entrypoint=entrypoint,
        name="game",
        output_dir=project_root / "dist",
        assets=(assets,),
    )

    with pytest.raises(ConfigurationError, match="inside project_root"):
        config.validate()


def test_config_rejects_non_boolean_embed_assets(tmp_path: Path) -> None:
    (tmp_path / "game.py").write_text("def main(): pass\n", encoding="utf-8")
    (tmp_path / "assets").mkdir()

    with pytest.raises(ConfigurationError, match="must be a boolean"):
        BuildConfig.from_mapping(
            {
                "entrypoint": "game.py",
                "name": "game",
                "assets": ["assets"],
                "embed_assets": "false",
            },
            project_root=tmp_path,
        )


def test_config_rejects_output_inside_asset_directory(tmp_path: Path) -> None:
    config = _target_config(tmp_path)
    unsafe_config = replace(config, output_dir=config.assets[0] / "generated")

    with pytest.raises(ConfigurationError, match="inside an asset directory"):
        unsafe_config.validate()


def test_web_source_zip_excludes_custom_output_directory(tmp_path: Path) -> None:
    config = replace(_target_config(tmp_path), output_dir=tmp_path / "generated")
    stale_output = config.output_dir / "web"
    stale_output.mkdir(parents=True)
    (stale_output / "must-not-ship.py").write_text("SECRET = True\n", encoding="utf-8")
    source_zip = tmp_path / "game.zip"

    web_module._build_source_zip(config, source_zip)

    with zipfile.ZipFile(source_zip) as archive:
        assert "generated/web/must-not-ship.py" not in archive.namelist()


def test_web_service_worker_uses_scoped_revisioned_cache(tmp_path: Path) -> None:
    config = _target_config(tmp_path)

    source = web_module._service_worker(config, revision="build-id")

    assert 'const REVISION="0.1.0-build-id";' in source
    assert "self.registration.scope" in source
    assert "key.startsWith(CACHE_PREFIX) && key !== CACHE" in source
    assert "caches.open(CACHE).then(cache => cache.match(event.request)" in source


def test_web_pyodide_version_is_encoded_as_one_url_segment() -> None:
    source = web_module._index_html(
        title="Game",
        pyodide_version='314.0.0\"><script src="bad.js',
    )

    assert '<script src="bad.js' not in source
    assert "%22%3E%3Cscript%20src%3D%22bad.js" in source


def test_web_target_publishes_staged_output_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _target_config(tmp_path)
    target_dir = config.output_dir / "web"
    target_dir.mkdir(parents=True)
    (target_dir / "obsolete.txt").write_text("old", encoding="utf-8")

    monkeypatch.setattr(web_module, "build_asset_pack", _fake_asset_pack)
    artifact = web_module.WebTarget().build(config)

    assert artifact.output_path == target_dir / "index.html"
    assert artifact.manifest_path == target_dir / "release.json"
    assert artifact.output_path.is_file()
    assert artifact.manifest_path.is_file()
    assert not (target_dir / "obsolete.txt").exists()
    _assert_no_transaction_residue(target_dir)


def test_web_target_preserves_previous_output_when_build_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _target_config(tmp_path)
    target_dir = config.output_dir / "web"
    target_dir.mkdir(parents=True)
    marker = target_dir / "current-build.txt"
    marker.write_text("still valid", encoding="utf-8")

    def fail_source_bundle(_config: BuildConfig, _output: Path) -> None:
        raise BuilderError("source bundle failed")

    monkeypatch.setattr(web_module, "build_asset_pack", _fake_asset_pack)
    monkeypatch.setattr(web_module, "_build_source_zip", fail_source_bundle)

    with pytest.raises(BuilderError, match="source bundle failed"):
        web_module.WebTarget().build(config)

    assert marker.read_text(encoding="utf-8") == "still valid"
    assert list(target_dir.iterdir()) == [marker]
    _assert_no_transaction_residue(target_dir)


def test_windows_target_publishes_staged_output_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _target_config(tmp_path)
    target_dir = config.output_dir / "windows"
    target_dir.mkdir(parents=True)
    (target_dir / "obsolete.txt").write_text("old", encoding="utf-8")
    _enable_fake_windows_build(monkeypatch, returncode=0)

    artifact = windows_module.WindowsTarget().build(config)

    assert artifact.output_path == target_dir / "game.exe"
    assert artifact.manifest_path == target_dir / "release.json"
    assert artifact.output_path.read_bytes() == b"new executable"
    assert (target_dir / "game.assets").is_file()
    assert artifact.manifest_path.is_file()
    assert not (target_dir / "obsolete.txt").exists()
    assert not (target_dir / ".work").exists()
    _assert_no_transaction_residue(target_dir)


def test_windows_target_preserves_matching_previous_files_when_nuitka_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _target_config(tmp_path)
    target_dir = config.output_dir / "windows"
    target_dir.mkdir(parents=True)
    executable = target_dir / "game.exe"
    asset_pack = target_dir / "game.assets"
    manifest = target_dir / "release.json"
    executable.write_bytes(b"old executable")
    asset_pack.write_bytes(b"old assets")
    manifest.write_text("old manifest", encoding="utf-8")
    _enable_fake_windows_build(monkeypatch, returncode=1)

    with pytest.raises(BuilderError, match="Nuitka build failed") as error:
        windows_module.WindowsTarget().build(config)

    assert "fake Nuitka diagnostics" in str(error.value)
    assert executable.read_bytes() == b"old executable"
    assert asset_pack.read_bytes() == b"old assets"
    assert manifest.read_text(encoding="utf-8") == "old manifest"
    _assert_no_transaction_residue(target_dir)


def test_staged_output_rolls_back_when_publish_rename_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "web"
    destination.mkdir()
    marker = destination / "current-build.txt"
    marker.write_text("old", encoding="utf-8")
    real_replace = staging_module.os.replace
    replace_calls = 0

    def fail_new_directory_publish(source: Path, target: Path) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("simulated publish failure")
        real_replace(source, target)

    monkeypatch.setattr(staging_module.os, "replace", fail_new_directory_publish)

    with pytest.raises(BuilderError, match="Could not publish"):
        with staged_output_directory(destination) as stage:
            (stage / "new-build.txt").write_text("new", encoding="utf-8")

    assert marker.read_text(encoding="utf-8") == "old"
    assert not (destination / "new-build.txt").exists()
    _assert_no_transaction_residue(destination)


def test_staged_output_recovers_backup_left_by_interrupted_publish(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "web"
    previous = tmp_path / ".web.previous"
    previous.mkdir()
    (previous / "current-build.txt").write_text("old", encoding="utf-8")

    with pytest.raises(BuilderError, match="next build failed"):
        with staged_output_directory(destination):
            assert (destination / "current-build.txt").is_file()
            raise BuilderError("next build failed")

    assert (destination / "current-build.txt").read_text(encoding="utf-8") == "old"
    _assert_no_transaction_residue(destination)


def test_staged_output_rejects_concurrent_writer(tmp_path: Path) -> None:
    destination = tmp_path / "web"

    with staged_output_directory(destination) as stage:
        (stage / "build.txt").write_text("complete", encoding="utf-8")
        with pytest.raises(BuilderError, match="Another build"):
            with staged_output_directory(destination):
                pass

    assert (destination / "build.txt").read_text(encoding="utf-8") == "complete"
    _assert_no_transaction_residue(destination)


def _target_config(tmp_path: Path) -> BuildConfig:
    entrypoint = tmp_path / "game.py"
    entrypoint.write_text("def main(): pass\n", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "sprite.txt").write_text("asset", encoding="utf-8")
    return BuildConfig(
        project_root=tmp_path,
        entrypoint=entrypoint,
        name="game",
        output_dir=tmp_path / "dist",
        assets=(assets,),
    )


def _enable_fake_windows_build(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returncode: int,
) -> None:
    monkeypatch.setattr(windows_module.sys, "platform", "win32")
    monkeypatch.setattr(windows_module, "_module_available", lambda _name: True)
    monkeypatch.setattr(windows_module, "build_asset_pack", _fake_asset_pack)

    def fake_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if returncode == 0:
            output_dir = Path(
                next(
                    value.split("=", 1)[1]
                    for value in command
                    if value.startswith("--output-dir=")
                )
            )
            output_name = next(
                value.split("=", 1)[1]
                for value in command
                if value.startswith("--output-filename=")
            )
            (output_dir / output_name).write_bytes(b"new executable")
        else:
            diagnostics = _kwargs["stdout"]
            diagnostics.write(b"fake Nuitka diagnostics")  # type: ignore[attr-defined]
        return SimpleNamespace(
            returncode=returncode,
            stdout="fake stdout",
            stderr="fake stderr",
        )

    monkeypatch.setattr(windows_module.subprocess, "run", fake_run)


def _fake_asset_pack(
    _roots: tuple[Path, ...],
    output_path: Path,
    *,
    project_root: Path,
) -> AssetPack:
    del project_root
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"fake encrypted assets")
    return AssetPack(output_path, b"0" * 32, ("assets/sprite.txt",))


def _assert_no_transaction_residue(target_dir: Path) -> None:
    assert not target_dir.with_name(f".{target_dir.name}.previous").exists()
    assert not list(target_dir.parent.glob(f".{target_dir.name}.stage-*"))
