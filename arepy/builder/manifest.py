"""Release manifest generation for incremental update systems."""

import hashlib
import json
from pathlib import Path


def write_release_manifest(
    output_path: Path,
    *,
    name: str,
    version: str,
    target: str,
    files: list[Path],
) -> Path:
    """Write a stable JSON manifest containing hashes for distributable files."""

    root = output_path.parent
    payload = {
        "schema": 1,
        "name": name,
        "version": version,
        "target": target,
        "files": [
            {
                "path": file.relative_to(root).as_posix(),
                "size": file.stat().st_size,
                "sha256": _sha256(file),
            }
            for file in sorted(files)
        ],
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
