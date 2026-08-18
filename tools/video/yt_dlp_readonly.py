#!/usr/bin/env python3
"""Run yt-dlp without letting it write the repository Cookie jar.

yt-dlp's ``--cookies FILE`` option is read/write: the in-memory jar is dumped
back to ``FILE`` when ``YoutubeDL.close()`` runs.  This wrapper therefore opens
the user-managed repository jar read-only, copies it to a private temporary
directory outside the repository, and gives only that disposable copy to
yt-dlp.

The canonical jar does not require an immutable filesystem flag. Repository
instructions reserve installation and replacement for the user; this wrapper
still enforces owner, mode, link, size, and race checks before snapshotting.

Usage::

    python3 tools/video/yt_dlp_readonly.py -- <yt-dlp arguments>
"""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Iterator, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_COOKIE = REPO_ROOT / "all_cookies.txt"
MAX_COOKIE_BYTES = 16 * 1024 * 1024
ALLOWED_MODES = frozenset((0o400, 0o600))
HELP_TEXT = """Usage:
  python3 tools/video/yt_dlp_readonly.py -- <yt-dlp arguments>

Runs yt-dlp with a private disposable copy of the protected Cookie jar.
Caller-supplied Cookie and configuration options are rejected.
"""


class CookieGuardError(RuntimeError):
    """A redacted, user-actionable Cookie safety failure."""


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_metadata(
    info: os.stat_result,
    *,
    expected_uid: int,
) -> None:
    mode = stat.S_IMODE(info.st_mode)
    if not stat.S_ISREG(info.st_mode):
        raise CookieGuardError("protected Cookie input is not a regular file")
    if info.st_uid != expected_uid:
        raise CookieGuardError("protected Cookie input has an unexpected owner")
    if info.st_nlink != 1:
        raise CookieGuardError("protected Cookie input has an unsafe link count")
    if mode not in ALLOWED_MODES:
        raise CookieGuardError("protected Cookie input has unsafe permissions")
    if info.st_size <= 0 or info.st_size > MAX_COOKIE_BYTES:
        raise CookieGuardError("protected Cookie input has an unsafe size")


def _open_canonical(
    canonical: Path,
    *,
    expected_uid: int,
) -> tuple[int, os.stat_result]:
    """Open and validate the canonical jar without following a symlink."""

    try:
        before = canonical.lstat()
    except OSError as error:
        raise CookieGuardError("protected Cookie input is unavailable") from error

    _validate_metadata(
        before,
        expected_uid=expected_uid,
    )

    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(canonical, flags)
    except OSError as error:
        raise CookieGuardError("protected Cookie input could not be opened safely") from error

    try:
        opened = os.fstat(descriptor)
        _validate_metadata(
            opened,
            expected_uid=expected_uid,
        )
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise CookieGuardError("protected Cookie input changed while opening")
        return descriptor, opened
    except BaseException:
        os.close(descriptor)
        raise


def _copy_descriptor(source_fd: int, destination_fd: int, expected_size: int) -> None:
    copied = 0
    while True:
        chunk = os.read(source_fd, 1024 * 1024)
        if not chunk:
            break
        view = memoryview(chunk)
        while view:
            written = os.write(destination_fd, view)
            if written <= 0:
                raise CookieGuardError("temporary Cookie snapshot could not be written")
            copied += written
            view = view[written:]
    if copied != expected_size:
        raise CookieGuardError("protected Cookie input changed while copying")
    os.fsync(destination_fd)


@contextlib.contextmanager
def private_cookie_snapshot(
    canonical: Path | str = CANONICAL_COOKIE,
    *,
    repo_root: Path | str = REPO_ROOT,
    temp_parent: Path | str | None = None,
    expected_uid: int | None = None,
) -> Iterator[Path]:
    """Yield a disposable, private copy of the protected Cookie jar."""

    canonical_path = Path(canonical)
    root = Path(repo_root).resolve(strict=True)
    owner_uid = os.getuid() if expected_uid is None else expected_uid

    source_fd, source_info = _open_canonical(
        canonical_path,
        expected_uid=owner_uid,
    )
    temporary_directory: Path | None = None
    try:
        parent = None if temp_parent is None else str(Path(temp_parent))
        temporary_directory = Path(
            tempfile.mkdtemp(prefix="cc-media-cookie-", dir=parent)
        )
        os.chmod(temporary_directory, 0o700)
        resolved_temporary = temporary_directory.resolve(strict=True)
        if _is_within(resolved_temporary, root):
            raise CookieGuardError("temporary Cookie storage is inside the repository")

        snapshot = temporary_directory / "cookies.txt"
        destination_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        destination_flags |= getattr(os, "O_CLOEXEC", 0)
        destination_flags |= getattr(os, "O_NOFOLLOW", 0)
        destination_fd = os.open(snapshot, destination_flags, 0o600)
        try:
            os.fchmod(destination_fd, 0o600)
            _copy_descriptor(source_fd, destination_fd, source_info.st_size)
        finally:
            os.close(destination_fd)

        after = os.fstat(source_fd)
        stable_fields = (
            "st_dev",
            "st_ino",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
        if any(getattr(after, field) != getattr(source_info, field) for field in stable_fields):
            raise CookieGuardError("protected Cookie input changed while copying")
        if stat.S_IMODE(snapshot.stat().st_mode) != 0o600:
            raise CookieGuardError("temporary Cookie snapshot has unsafe permissions")
        yield snapshot
    finally:
        os.close(source_fd)
        if temporary_directory is not None:
            shutil.rmtree(temporary_directory, ignore_errors=True)


def _validate_yt_dlp_arguments(arguments: Sequence[str], canonical: Path) -> list[str]:
    if not arguments:
        raise CookieGuardError("no yt-dlp arguments were provided")
    safe: list[str] = []
    protected_name = canonical.name
    protected_path = str(canonical)
    try:
        protected_resolved = str(canonical.resolve(strict=False))
    except OSError:
        protected_resolved = protected_path
    for argument in arguments:
        if not isinstance(argument, str) or not argument:
            raise CookieGuardError("yt-dlp arguments are invalid")
        lowered = argument.lower()
        if (
            lowered.startswith("--cookie")
            or lowered.startswith("--no-cookie")
            or lowered.startswith("--config")
            or lowered.startswith("--no-config")
            or lowered == "--ignore-config"
        ):
            raise CookieGuardError("caller-supplied Cookie or config options are forbidden")
        folded = argument.casefold()
        if (
            protected_name.casefold() in folded
            or protected_path.casefold() in folded
            or protected_resolved.casefold() in folded
        ):
            raise CookieGuardError("a yt-dlp argument references the protected Cookie input")
        safe.append(argument)
    return safe


def run_yt_dlp(
    arguments: Sequence[str],
    *,
    canonical: Path | str = CANONICAL_COOKIE,
    repo_root: Path | str = REPO_ROOT,
    temp_parent: Path | str | None = None,
    expected_uid: int | None = None,
    executable: str = "yt-dlp",
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    """Run yt-dlp against a temporary Cookie copy and return its exit code."""

    canonical_path = Path(canonical)
    safe_arguments = _validate_yt_dlp_arguments(arguments, canonical_path)
    with private_cookie_snapshot(
        canonical_path,
        repo_root=repo_root,
        temp_parent=temp_parent,
        expected_uid=expected_uid,
    ) as snapshot:
        command = [
            executable,
            "--ignore-config",
            "--no-config-locations",
            "--cookies",
            str(snapshot),
            *safe_arguments,
        ]
        completed = runner(command, check=False)
        return int(completed.returncode)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments in (["-h"], ["--help"]):
        print(HELP_TEXT, end="")
        return 0
    if not arguments or arguments[0] != "--":
        print(
            "YTDLP COOKIE GUARD: FAIL - invoke this wrapper with a -- delimiter",
            file=sys.stderr,
        )
        return 2
    try:
        return run_yt_dlp(arguments[1:])
    except CookieGuardError as error:
        print(f"YTDLP COOKIE GUARD: FAIL - {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except OSError:
        print("YTDLP COOKIE GUARD: FAIL - local execution error", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
