#!/usr/bin/env python3
"""Non-blocking adaptive CPU budgets for cc-media heavy workers.

Every heavy process publishes a small PID/start-time marker, immediately counts
the currently live markers, and then starts.  There is deliberately no lock,
queue, semaphore, polling loop, or cross-goal wait.  The first live worker gets
4 threads, the second 3, and later workers 2.  A valid explicit override wins
but is still limited to 1..4.

Markers contain no project path, slug, prompt, or media metadata.  They live in
a private per-user, per-repository directory under /tmp and are validated
against the operating system's process start identity so SIGKILL leftovers and
reused PIDs do not keep future goals throttled.
"""

from __future__ import annotations

import argparse
import atexit
import ctypes
import errno
import hashlib
import json
import os
import secrets
import stat
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, MutableMapping, Optional, Sequence


ASR_THREADS_ENV = "CC_MEDIA_ASR_THREADS"
ASR_INTEROP_THREADS_ENV = "CC_MEDIA_ASR_INTEROP_THREADS"
FFMPEG_THREADS_ENV = "CC_MEDIA_FFMPEG_THREADS"
HYPERFRAMES_WORKERS_ENV = "CC_MEDIA_HYPERFRAMES_WORKERS"
DEFAULT_SAFE_THREADS = 2
DEFAULT_ASR_INTEROP_THREADS = 1
MAX_THREADS = 4
THREAD_TOKEN = "__CC_MEDIA_THREADS__"
MARKER_SCHEMA = 1
MAX_MARKER_BYTES = 2048

_INTRA_OP_ENV_KEYS = (
    "OMP_NUM_THREADS",
    "OMP_THREAD_LIMIT",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    uid: int
    start_primary: int
    start_secondary: int


@dataclass(frozen=True)
class ASRResourceBudget:
    threads: int
    interop_threads: int


class ResourceLease:
    """An already-published, non-blocking activity marker and its decision."""

    def __init__(
        self,
        *,
        threads: int,
        active_workers: int,
        marker: Path | None = None,
        marker_identity: tuple[int, int] | None = None,
        adaptive: bool = True,
    ) -> None:
        self.threads = threads
        self.active_workers = active_workers
        self.adaptive = adaptive
        self._marker = marker
        self._marker_identity = marker_identity
        self._closed = False

    def __enter__(self) -> "ResourceLease":
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        marker = self._marker
        if marker is None:
            return
        try:
            current = marker.lstat()
            if (
                self._marker_identity is not None
                and (current.st_dev, current.st_ino) != self._marker_identity
            ):
                return
            if stat.S_ISREG(current.st_mode) and current.st_nlink == 1:
                marker.unlink(missing_ok=True)
        except OSError:
            # Cleanup is best-effort. A stale marker is rejected by start-time
            # validation during the next acquisition.
            return


IdentityReader = Callable[[int], Optional[ProcessIdentity]]
_ASR_LEASE: ResourceLease | None = None


def _bounded_override(
    environ: MutableMapping[str, str],
    name: str,
    *,
    explicit: int | str | None = None,
) -> int | None:
    raw: str | int | None = explicit
    if raw is None:
        raw = environ.get(name)
    if raw is None or raw == "":
        return None
    try:
        value = int(raw, 10) if isinstance(raw, str) else int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer from 1 to {MAX_THREADS}") from exc
    if value < 1 or value > MAX_THREADS:
        raise ValueError(f"{name} must be an integer from 1 to {MAX_THREADS}")
    return value


def _threads_for_count(active_workers: int) -> int:
    if active_workers <= 1:
        return 4
    if active_workers == 2:
        return 3
    return 2


def _darwin_process_identity(pid: int) -> ProcessIdentity | None:
    # struct proc_bsdinfo is 136 bytes on supported macOS versions. Relevant
    # ABI offsets: pid=12, uid=20, start_tvsec=120, start_tvusec=128.
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    proc_pidinfo = library.proc_pidinfo
    proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    proc_pidinfo.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(136)
    ctypes.set_errno(0)
    size = proc_pidinfo(pid, 3, 0, buffer, len(buffer))
    if size != len(buffer):
        error = ctypes.get_errno()
        if error in (errno.ESRCH, errno.ENOENT):
            return None
        raise OSError(error or errno.EIO, "proc_pidinfo failed")
    raw = buffer.raw
    status = struct.unpack_from("=I", raw, 4)[0]
    if status == 5:  # SZOMB
        return None
    actual_pid = struct.unpack_from("=I", raw, 12)[0]
    uid = struct.unpack_from("=I", raw, 20)[0]
    start_sec = struct.unpack_from("=Q", raw, 120)[0]
    start_usec = struct.unpack_from("=Q", raw, 128)[0]
    if actual_pid != pid or start_sec <= 0:
        raise OSError(errno.EIO, "proc_pidinfo returned an invalid identity")
    return ProcessIdentity(actual_pid, uid, start_sec, start_usec)


def _linux_process_identity(pid: int) -> ProcessIdentity | None:
    directory = Path("/proc") / str(pid)
    try:
        owner = directory.stat().st_uid
        raw = (directory / "stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    close = raw.rfind(")")
    if close < 0:
        raise OSError(errno.EIO, "invalid /proc stat record")
    fields = raw[close + 2 :].split()
    if len(fields) <= 19:
        raise OSError(errno.EIO, "short /proc stat record")
    if fields[0] == "Z":
        return None
    return ProcessIdentity(pid, owner, int(fields[19]), 0)


def process_identity(pid: int) -> ProcessIdentity | None:
    if sys.platform == "darwin":
        return _darwin_process_identity(pid)
    if sys.platform.startswith("linux"):
        return _linux_process_identity(pid)
    raise OSError(errno.ENOTSUP, "process start identity is unsupported")


def _default_registry_dir() -> Path:
    repository = Path(__file__).resolve().parents[2]
    repo_stat = repository.stat()
    identity = hashlib.sha256(
        f"{repository}:{repo_stat.st_dev}:{repo_stat.st_ino}".encode("utf-8")
    ).hexdigest()[:24]
    return Path("/tmp") / f"cc-media-resource-v1-{os.getuid()}" / identity


def _ensure_private_directory(path: Path, uid: int) -> None:
    parent = path.parent
    if path == _default_registry_dir():
        # Create and validate the per-user parent before the repo-specific leaf.
        parent.mkdir(mode=0o700, exist_ok=True)
        parent_stat = parent.lstat()
        if (
            not stat.S_ISDIR(parent_stat.st_mode)
            or parent_stat.st_uid != uid
            or stat.S_IMODE(parent_stat.st_mode) != 0o700
        ):
            raise OSError(errno.EPERM, "resource registry parent is not private")
    path.mkdir(mode=0o700, exist_ok=True)
    current = path.lstat()
    if (
        not stat.S_ISDIR(current.st_mode)
        or current.st_uid != uid
        or stat.S_IMODE(current.st_mode) != 0o700
    ):
        raise OSError(errno.EPERM, "resource registry is not private")


def _safe_unlink(path: Path, *, expected: tuple[int, int] | None = None) -> None:
    try:
        current = path.lstat()
        if expected is not None and (current.st_dev, current.st_ino) != expected:
            return
        if stat.S_ISREG(current.st_mode) and current.st_nlink == 1:
            path.unlink(missing_ok=True)
    except OSError:
        return


def _read_marker(path: Path, uid: int) -> tuple[dict[str, Any], tuple[int, int]] | None:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != uid
            or info.st_nlink != 1
            or info.st_size <= 0
            or info.st_size > MAX_MARKER_BYTES
            or stat.S_IMODE(info.st_mode) & 0o077
        ):
            return None
        data = os.read(descriptor, MAX_MARKER_BYTES + 1)
        if len(data) != info.st_size:
            return None
        value = json.loads(data.decode("utf-8"))
        if not isinstance(value, dict):
            return None
        return value, (info.st_dev, info.st_ino)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    finally:
        os.close(descriptor)


def _publish_marker(registry: Path, identity: ProcessIdentity, kind: str) -> tuple[Path, tuple[int, int]]:
    payload = {
        "schema": MARKER_SCHEMA,
        "kind": kind,
        "pid": identity.pid,
        "uid": identity.uid,
        "start_primary": identity.start_primary,
        "start_secondary": identity.start_secondary,
        "nonce": secrets.token_hex(16),
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    name = f"lease-{payload['nonce']}.json"
    marker = registry / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(marker, flags, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                raise OSError(errno.EIO, "resource marker write did not progress")
            offset += written
        os.fsync(descriptor)
        info = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    return marker, (info.st_dev, info.st_ino)


def acquire_resource_lease(
    kind: str,
    *,
    env_name: str,
    environ: MutableMapping[str, str] | None = None,
    explicit_threads: int | None = None,
    registry_dir: Path | None = None,
    identity_reader: IdentityReader = process_identity,
    pid: int | None = None,
) -> ResourceLease:
    """Publish immediately, count live workers, and return without waiting."""

    target = os.environ if environ is None else environ
    override = _bounded_override(target, env_name, explicit=explicit_threads)
    selected_pid = os.getpid() if pid is None else pid
    marker: Path | None = None
    marker_identity: tuple[int, int] | None = None
    try:
        current = identity_reader(selected_pid)
        if current is None or current.uid != os.getuid():
            raise OSError(errno.ESRCH, "current process identity is unavailable")
        registry = registry_dir or _default_registry_dir()
        _ensure_private_directory(registry, current.uid)
        marker, marker_identity = _publish_marker(registry, current, kind)
        active = 0
        for candidate in registry.iterdir():
            if not candidate.name.startswith("lease-") or not candidate.name.endswith(".json"):
                continue
            parsed = _read_marker(candidate, current.uid)
            if parsed is None:
                continue
            row, file_identity = parsed
            required = {
                "schema", "kind", "pid", "uid", "start_primary", "start_secondary", "nonce"
            }
            if set(row) != required or row.get("schema") != MARKER_SCHEMA:
                _safe_unlink(candidate, expected=file_identity)
                continue
            if (
                type(row.get("pid")) is not int
                or type(row.get("uid")) is not int
                or type(row.get("start_primary")) is not int
                or type(row.get("start_secondary")) is not int
                or not isinstance(row.get("kind"), str)
                or not isinstance(row.get("nonce"), str)
                or row.get("uid") != current.uid
            ):
                _safe_unlink(candidate, expected=file_identity)
                continue
            try:
                recorded = ProcessIdentity(
                    row["pid"],
                    row["uid"],
                    row["start_primary"],
                    row["start_secondary"],
                )
            except (TypeError, ValueError):
                _safe_unlink(candidate, expected=file_identity)
                continue
            live = identity_reader(recorded.pid)
            if live != recorded:
                _safe_unlink(candidate, expected=file_identity)
                continue
            active += 1
        threads = override if override is not None else _threads_for_count(active)
        return ResourceLease(
            threads=threads,
            active_workers=max(active, 1),
            marker=marker,
            marker_identity=marker_identity,
            adaptive=override is None,
        )
    except OSError:
        if marker is not None:
            _safe_unlink(marker, expected=marker_identity)
        return ResourceLease(
            threads=override if override is not None else DEFAULT_SAFE_THREADS,
            active_workers=0,
            adaptive=override is None,
        )


def resolve_ffmpeg_threads(**kwargs: Any) -> ResourceLease:
    return acquire_resource_lease("ffmpeg", env_name=FFMPEG_THREADS_ENV, **kwargs)


def resolve_hyperframes_workers(**kwargs: Any) -> ResourceLease:
    return acquire_resource_lease(
        "hyperframes", env_name=HYPERFRAMES_WORKERS_ENV, **kwargs
    )


def configure_asr_environment(
    environ: MutableMapping[str, str] | None = None,
) -> ASRResourceBudget:
    """Apply an ASR budget before numeric imports and hold its process lease."""

    global _ASR_LEASE
    target = os.environ if environ is None else environ
    if environ is None:
        if _ASR_LEASE is None:
            _ASR_LEASE = acquire_resource_lease(
                "asr", env_name=ASR_THREADS_ENV, environ=target
            )
            atexit.register(_ASR_LEASE.close)
        threads = _ASR_LEASE.threads
    else:
        # Pure mapping calls are deterministic and side-effect free for tests and
        # embedded callers. Production entrypoints call without this argument.
        threads = _bounded_override(target, ASR_THREADS_ENV) or DEFAULT_SAFE_THREADS
    interop = _bounded_override(target, ASR_INTEROP_THREADS_ENV) or DEFAULT_ASR_INTEROP_THREADS
    text_threads = str(threads)
    for key in _INTRA_OP_ENV_KEYS:
        target[key] = text_threads
    target["TOKENIZERS_PARALLELISM"] = "false"
    return ASRResourceBudget(threads=threads, interop_threads=interop)


def configure_torch_runtime(torch_module: Any, budget: ASRResourceBudget) -> None:
    torch_module.set_num_threads(budget.threads)
    try:
        torch_module.set_num_interop_threads(budget.interop_threads)
    except RuntimeError:
        if torch_module.get_num_interop_threads() != budget.interop_threads:
            raise


def _hyperframes_explicit_workers(command: Sequence[str]) -> int | None:
    values: list[str] = []
    index = 0
    while index < len(command):
        value = command[index]
        if value == "--workers":
            if index + 1 >= len(command):
                raise ValueError("--workers requires a value from 1 to 4")
            values.append(command[index + 1])
            index += 2
            continue
        if value.startswith("--workers="):
            values.append(value.split("=", 1)[1])
        index += 1
    if len(values) > 1:
        raise ValueError("--workers may be specified only once")
    if not values:
        return None
    return _bounded_override({}, "--workers", explicit=values[0])


def _exec_with_lease(command: list[str], lease: ResourceLease) -> int:
    if not command:
        lease.close()
        raise ValueError("a child command is required")
    rendered = [str(lease.threads) if value == THREAD_TOKEN else value for value in command]
    try:
        os.execvpe(rendered[0], rendered, os.environ.copy())
    except OSError:
        lease.close()
        raise
    return 127


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    ffmpeg = subparsers.add_parser("ffmpeg", help="exec one FFmpeg command with an adaptive lease")
    ffmpeg.add_argument("command", nargs=argparse.REMAINDER)
    hyperframes = subparsers.add_parser(
        "hyperframes", help="exec one HyperFrames render with adaptive --workers"
    )
    hyperframes.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if args.mode == "ffmpeg":
        return _exec_with_lease(command, resolve_ffmpeg_threads())
    explicit = _hyperframes_explicit_workers(command)
    lease = acquire_resource_lease(
        "hyperframes",
        env_name=HYPERFRAMES_WORKERS_ENV,
        explicit_threads=explicit,
    )
    if explicit is None:
        command.extend(["--workers", str(lease.threads)])
    return _exec_with_lease(command, lease)


def main() -> int:
    try:
        return cli()
    except (OSError, ValueError) as exc:
        print(f"RESOURCE BUDGET: FAIL — {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
