"""Transactional publication helpers for builder target directories."""

from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator

from .errors import BuilderError


@contextmanager
def staged_output_directory(destination: Path) -> Iterator[Path]:
    """Build beside *destination* and publish it as one directory swap.

    The destination remains untouched while the caller populates the staging
    directory.  A short two-rename commit keeps the previous output available
    for rollback on platforms, such as Windows, that cannot replace a non-empty
    directory directly.
    """

    # Existing builders write through output symlinks.  Resolving here keeps
    # that behavior while still placing stage and backup on the same volume.
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = destination.with_name(f".{destination.name}.previous")

    with _destination_lock(destination):
        _recover_interrupted_publish(destination, previous)
        _remove_stale_stages(destination)
        stage = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.stage-",
                dir=destination.parent,
            )
        )
        try:
            yield stage
            _publish(stage, destination, previous)
        except BaseException:
            _remove_path(stage, ignore_errors=True)
            raise


def _publish(stage: Path, destination: Path, previous: Path) -> None:
    moved_previous = False
    try:
        if destination.exists():
            os.replace(destination, previous)
            moved_previous = True
        os.replace(stage, destination)
    except OSError as publish_error:
        if moved_previous and not destination.exists() and previous.exists():
            try:
                os.replace(previous, destination)
            except OSError as rollback_error:
                raise BuilderError(
                    "Could not publish the new build or restore the previous output. "
                    f"The recoverable backup remains at: {previous}"
                ) from rollback_error
        raise BuilderError(
            f"Could not publish the staged build to: {destination}"
        ) from publish_error

    # The new directory is already live.  If cleanup is interrupted, the next
    # build recognizes this state and removes the obsolete backup.
    _remove_path(previous, ignore_errors=True)


def _recover_interrupted_publish(destination: Path, previous: Path) -> None:
    if not previous.exists():
        return
    if destination.exists():
        _remove_path(previous)
        return
    try:
        os.replace(previous, destination)
    except OSError as error:
        raise BuilderError(
            f"Could not restore the previous build output from: {previous}"
        ) from error


def _remove_stale_stages(destination: Path) -> None:
    pattern = f".{destination.name}.stage-*"
    for stale_stage in destination.parent.glob(pattern):
        _remove_path(stale_stage)


def _remove_path(path: Path, *, ignore_errors: bool = False) -> None:
    try:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
    except OSError:
        if not ignore_errors:
            raise


@contextmanager
def _destination_lock(destination: Path) -> Iterator[None]:
    """Hold a process-scoped advisory lock for one target destination."""

    lock_path = destination.with_name(f".{destination.name}.build.lock")
    lock_file = lock_path.open("a+b")
    try:
        _lock_file(lock_file, destination)
        yield
    finally:
        _unlock_file(lock_file)
        lock_file.close()


def _lock_file(lock_file: BinaryIO, destination: Path) -> None:
    lock_file.seek(0, os.SEEK_END)
    if lock_file.tell() == 0:
        lock_file.write(b"\0")
        lock_file.flush()
    lock_file.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        lock_file.close()
        raise BuilderError(
            f"Another build is already publishing to: {destination}"
        ) from error


def _unlock_file(lock_file: BinaryIO) -> None:
    if lock_file.closed:
        return
    lock_file.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except OSError:
        # Process exit also releases the advisory lock.  Do not mask a build
        # error merely because explicit unlock failed.
        pass
