import sys
from pathlib import Path

import pytest

from arepy.runtime_assets import resolve_asset_path


def test_web_zip_asset_resolves_to_decrypted_filesystem_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = Path("/assets/bunny.png")
    monkeypatch.setenv("AREPY_PLATFORM", "web")
    monkeypatch.setattr(sys, "path", ["/game.zip"])
    monkeypatch.setattr(Path, "is_file", lambda path: path == expected)

    resolved = resolve_asset_path("/game.zip/assets/bunny.png")

    assert resolved == expected


def test_web_zip_asset_drops_source_module_directories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = Path("/assets/bunny.png")
    monkeypatch.setenv("AREPY_PLATFORM", "web")
    monkeypatch.setattr(sys, "path", ["/game.zip"])
    monkeypatch.setattr(Path, "is_file", lambda path: path == expected)

    resolved = resolve_asset_path("/game.zip/examples/assets/bunny.png")

    assert resolved == expected


def test_web_zip_asset_prefers_the_longest_existing_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact = Path("/examples/assets/bunny.png")
    fallback = Path("/assets/bunny.png")
    monkeypatch.setenv("AREPY_PLATFORM", "web")
    monkeypatch.setattr(sys, "path", ["/game.zip"])
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: path in {exact, fallback},
    )

    resolved = resolve_asset_path("/game.zip/examples/assets/bunny.png")

    assert resolved == exact


def test_web_zip_asset_rejects_archive_that_is_not_an_import_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = Path("/other.zip/assets/bunny.png")
    monkeypatch.setenv("AREPY_PLATFORM", "web")
    monkeypatch.setattr(sys, "path", ["/game.zip"])
    monkeypatch.setattr(Path, "is_file", lambda _path: True)

    assert resolve_asset_path(requested) == requested


def test_web_zip_asset_rejects_parent_traversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = Path("/game.zip/assets/../../private.txt")
    monkeypatch.setenv("AREPY_PLATFORM", "web")
    monkeypatch.setattr(sys, "path", ["/game.zip"])
    monkeypatch.setattr(Path, "is_file", lambda _path: True)

    assert resolve_asset_path(requested) == requested


def test_desktop_does_not_remap_zip_shaped_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = Path("/game.zip/assets/bunny.png")
    monkeypatch.delenv("AREPY_PLATFORM", raising=False)
    monkeypatch.setattr(sys, "path", ["/game.zip"])
    monkeypatch.setattr(Path, "is_file", lambda _path: True)

    assert resolve_asset_path(requested) == requested
