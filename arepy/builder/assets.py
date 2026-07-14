"""Authenticated asset archive creation."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .errors import ToolUnavailableError

MAGIC = b"ARPK\x01"
_PAYLOAD_SPOOL_LIMIT = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class AssetPack:
    """Generated encrypted archive and its runtime key."""

    path: Path
    key: bytes
    entries: tuple[str, ...]

    @property
    def encoded_key(self) -> str:
        """Return the key in the transport format used by launchers."""

        return base64.urlsafe_b64encode(self.key).decode("ascii")


def build_asset_pack(
    roots: tuple[Path, ...],
    output_path: Path,
    *,
    project_root: Path,
) -> AssetPack:
    """Encrypt all asset roots into a deterministic-path AES-GCM container."""

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as error:
        raise ToolUnavailableError(
            "Asset packing requires the 'builder' extra: pip install 'arepy[builder]'"
        ) from error

    files = _collect_files(
        roots,
        project_root,
        excluded_path=output_path,
    )
    key = AESGCM.generate_key(bit_length=256)
    cipher = AESGCM(key)
    entries: list[dict[str, object]] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.SpooledTemporaryFile(
        max_size=_PAYLOAD_SPOOL_LIMIT,
        mode="w+b",
        dir=output_path.parent,
    ) as payload:
        for logical_path, source_path in files:
            plaintext = source_path.read_bytes()
            nonce = os.urandom(12)
            ciphertext = cipher.encrypt(
                nonce,
                plaintext,
                logical_path.encode("utf-8"),
            )
            offset = payload.tell()
            payload.write(ciphertext)
            entries.append(
                {
                    "path": logical_path,
                    "offset": offset,
                    "length": len(ciphertext),
                    "nonce": base64.b64encode(nonce).decode("ascii"),
                    "sha256": hashlib.sha256(plaintext).hexdigest(),
                    "size": len(plaintext),
                }
            )
            del plaintext, ciphertext

        header = json.dumps(
            {"version": 1, "algorithm": "AES-256-GCM", "entries": entries},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        payload.seek(0)
        with output_path.open("wb") as output:
            output.write(MAGIC)
            output.write(struct.pack("<I", len(header)))
            output.write(header)
            shutil.copyfileobj(payload, output, length=1024 * 1024)

    return AssetPack(output_path, key, tuple(item[0] for item in files))


def _collect_files(
    roots: tuple[Path, ...],
    project_root: Path,
    *,
    excluded_path: Path | None = None,
) -> list[tuple[str, Path]]:
    collected: dict[str, Path] = {}
    for root in roots:
        candidates = (root,) if root.is_file() else root.rglob("*")
        for path in candidates:
            if path == excluded_path or not path.is_file():
                continue
            logical = (
                root.name
                if root.is_file()
                else (Path(root.name) / path.relative_to(root)).as_posix()
            )
            if logical in collected:
                raise ValueError(f"Duplicate asset path in pack: {logical}")
            collected[logical] = path
    return sorted(collected.items())
