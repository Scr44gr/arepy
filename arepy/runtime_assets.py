"""Resolve development paths and encrypted builder asset paths uniformly."""

from __future__ import annotations

import atexit
import base64
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
from functools import lru_cache
from pathlib import Path, PurePosixPath

_MAGIC = b"ARPK\x01"
_EXTRACTED: dict[str, Path] = {}
_TEMP_ROOT: Path | None = None


def resolve_asset_path(path: str | os.PathLike[str]) -> Path:
    """Return a real path for a development or packed asset."""

    requested = Path(path)
    if requested.exists():
        return requested

    web_asset = _resolve_web_zip_asset(requested)
    if web_asset is not None:
        return web_asset

    pack_value = os.getenv("AREPY_ASSET_PACK")
    key_value = os.getenv("AREPY_ASSET_KEY")
    if not pack_value or not key_value:
        return requested

    logical_path = _normalize_asset_path(requested)
    cached = _EXTRACTED.get(logical_path)
    if cached is not None:
        return cached

    pack_path = Path(pack_value)
    entries, payload_offset = _read_pack_index(pack_path)
    entry = entries.get(logical_path)
    if entry is None:
        suffix_matches = [
            candidate
            for candidate in entries
            if candidate.endswith(f"/{logical_path}")
        ]
        if len(suffix_matches) == 1:
            logical_path = suffix_matches[0]
            entry = entries[logical_path]
    if entry is None:
        return requested

    plaintext = _decrypt_entry(pack_path, key_value, logical_path, entry, payload_offset)
    output = _temporary_root() / logical_path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(plaintext)
    _EXTRACTED[logical_path] = output
    return output


def _resolve_web_zip_asset(requested: Path) -> Path | None:
    """Map a zipimport path to the decrypted Pyodide filesystem asset."""

    if os.getenv("AREPY_PLATFORM") != "web":
        return None

    web_path = PurePosixPath(requested.as_posix())
    parts = web_path.parts
    if not web_path.is_absolute() or ".." in parts:
        return None

    for index, part in enumerate(parts):
        if PurePosixPath(part).suffix.casefold() != ".zip":
            continue

        archive = PurePosixPath(*parts[: index + 1]).as_posix()
        if not _is_active_zip_import(archive):
            continue

        relative_parts = parts[index + 1 :]
        if not relative_parts:
            return None

        # Source modules keep their directory inside ``game.zip``, while each
        # configured asset root is extracted from its own basename.  Try the
        # exact zip-relative path first, then progressively remove only leading
        # source-module directories.  The longest existing suffix wins.
        for start in range(len(relative_parts)):
            candidate = Path("/").joinpath(*relative_parts[start:])
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                return None
        return None

    return None


def _is_active_zip_import(archive: str) -> bool:
    for import_root in sys.path:
        try:
            normalized = os.fspath(import_root).replace("\\", "/").rstrip("/")
        except TypeError:
            continue
        if normalized == archive:
            return True
    return False


def _normalize_asset_path(path: Path) -> str:
    value = path.as_posix()
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


@lru_cache(maxsize=4)
def _read_pack_index(
    pack_path: Path,
) -> tuple[dict[str, dict[str, object]], int]:
    with pack_path.open("rb") as source:
        if source.read(len(_MAGIC)) != _MAGIC:
            raise RuntimeError(f"Invalid Arepy asset pack: {pack_path}")
        raw_header_size = source.read(4)
        if len(raw_header_size) != 4:
            raise RuntimeError(f"Truncated Arepy asset pack: {pack_path}")
        header_size = struct.unpack("<I", raw_header_size)[0]
        header = json.loads(source.read(header_size))
    entries = {entry["path"]: entry for entry in header["entries"]}
    return entries, len(_MAGIC) + 4 + header_size


def _decrypt_entry(
    pack_path: Path,
    encoded_key: str,
    logical_path: str,
    entry: dict[str, object],
    payload_offset: int,
) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as error:
        raise RuntimeError(
            "This build contains encrypted assets but cryptography is unavailable."
        ) from error

    key = base64.urlsafe_b64decode(encoded_key)
    nonce = base64.b64decode(str(entry["nonce"]))
    offset = int(entry["offset"])
    length = int(entry["length"])
    with pack_path.open("rb") as source:
        source.seek(payload_offset + offset)
        ciphertext = source.read(length)
    plaintext = AESGCM(key).decrypt(
        nonce,
        ciphertext,
        logical_path.encode("utf-8"),
    )
    if hashlib.sha256(plaintext).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"Asset integrity verification failed: {logical_path}")
    return plaintext


def _temporary_root() -> Path:
    global _TEMP_ROOT
    if _TEMP_ROOT is None:
        _TEMP_ROOT = Path(tempfile.mkdtemp(prefix="arepy-assets-"))
        atexit.register(shutil.rmtree, _TEMP_ROOT, ignore_errors=True)
    return _TEMP_ROOT
