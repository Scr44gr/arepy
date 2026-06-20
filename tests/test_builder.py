import json
from pathlib import Path

import pytest

from arepy.builder.assets import build_asset_pack
from arepy.builder.cli import _unique_targets, create_parser
from arepy.builder.config import BuildConfig
from arepy.builder.core import Builder
from arepy.builder.models import BuildArtifact, BuildTarget
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
