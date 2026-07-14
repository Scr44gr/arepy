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
        "files": [_file_record(file, root) for file in sorted(files)],
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def _file_record(path: Path, root: Path) -> dict[str, str | int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return {
        "path": path.relative_to(root).as_posix(),
        "size": size,
        "sha256": digest.hexdigest(),
    }
