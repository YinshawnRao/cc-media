"""Fail-closed Qwen model verification receipts.

The expensive operation is a full SHA-256 pass over the pinned model tree.
`doctor.py --full-model-hash` performs it once and writes an ignored receipt.
Generation then validates the receipt against the current runtime, manifest,
model realpath, file set and per-file stat signatures without rereading 2 GB.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


RECEIPT_SCHEMA_VERSION = "1.1.0"
RECEIPT_KIND = "qwen-full-model-hash-receipt-v1"
PORTABLE_CLAIM_KIND = "qwen-model-portable-claim-v1"
TREE_DIGEST_PREFIX = b"poc-qa-tree-v1\0"
MANIFEST_DIRECTORY = "model-manifests"
RECEIPT_DIRECTORY = Path("runtime") / "model-verifications"
PORTABLE_CLAIM_KEYS = (
    "portable_claim_kind",
    "verification_kind",
    "model_id",
    "model_revision",
    "qwen_config_sha256",
    "manifest_sha256",
    "verified_model_tree_sha256",
    "model_file_count",
    "model_total_bytes",
    "mlx_audio_version",
)


class ProvenanceError(ValueError):
    """Raised when pinned runtime/model provenance cannot be proved."""


def _mode(value: os.stat_result) -> int:
    return stat.S_IMODE(value.st_mode)


def _trusted_stat(
    value: os.stat_result,
    label: str,
    *,
    expected_kind: str,
    exact_mode: int | None = None,
) -> None:
    expected = stat.S_ISDIR if expected_kind == "directory" else stat.S_ISREG
    if not expected(value.st_mode):
        article = "a directory" if expected_kind == "directory" else "a regular file"
        raise ProvenanceError(f"{label} is not {article}")
    if value.st_uid != os.getuid():
        raise ProvenanceError(f"{label} is not owned by the current user")
    current_mode = _mode(value)
    if exact_mode is not None:
        if current_mode != exact_mode:
            raise ProvenanceError(
                f"{label} mode must be {exact_mode:04o}, got {current_mode:04o}"
            )
    elif current_mode & 0o022:
        raise ProvenanceError(f"{label} must not be group/world writable")


def _lstat(path: Path, label: str) -> os.stat_result:
    try:
        value = path.lstat()
    except OSError as exc:
        raise ProvenanceError(f"cannot inspect {label}: {exc}") from exc
    if stat.S_ISLNK(value.st_mode):
        raise ProvenanceError(f"{label} must not be a symlink: {path}")
    return value


def _secure_directory_tree(
    trusted_root: Path,
    target: Path,
    *,
    create: bool,
    label: str,
) -> Path:
    trusted_root = Path(os.path.abspath(trusted_root))
    target = Path(os.path.abspath(target))
    try:
        relative = target.relative_to(trusted_root)
    except ValueError as exc:
        raise ProvenanceError(f"{label} is outside the trusted TTS root") from exc
    root_stat = _lstat(trusted_root, "trusted TTS root")
    _trusted_stat(root_stat, "trusted TTS root", expected_kind="directory")
    cursor = trusted_root
    for part in relative.parts:
        cursor = cursor / part
        try:
            value = cursor.lstat()
        except FileNotFoundError:
            if not create:
                raise ProvenanceError(f"{label} directory is missing: {cursor}")
            try:
                cursor.mkdir(mode=0o700)
            except OSError as exc:
                raise ProvenanceError(f"cannot create {label} directory: {exc}") from exc
            value = _lstat(cursor, label)
        except OSError as exc:
            raise ProvenanceError(f"cannot inspect {label} directory: {exc}") from exc
        if stat.S_ISLNK(value.st_mode):
            raise ProvenanceError(f"{label} parent must not be a symlink: {cursor}")
        _trusted_stat(value, f"{label} parent {cursor}", expected_kind="directory")
    return target


def _secure_read(
    path: Path,
    *,
    trusted_root: Path,
    label: str,
    exact_mode: int | None = None,
) -> tuple[bytes, os.stat_result]:
    path = Path(os.path.abspath(path))
    _secure_directory_tree(
        trusted_root,
        path.parent,
        create=False,
        label=label,
    )
    before = _lstat(path, label)
    _trusted_stat(before, label, expected_kind="file", exact_mode=exact_mode)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ProvenanceError(f"cannot open {label}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        _trusted_stat(opened, label, expected_kind="file", exact_mode=exact_mode)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ProvenanceError(f"{label} changed while opening")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            raw = handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    after = _lstat(path, label)
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
        opened.st_ctime_ns,
    ):
        raise ProvenanceError(f"{label} changed while reading")
    return raw, after


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    before = _lstat(path, f"model file {path.name}")
    _trusted_stat(before, f"model file {path.name}", expected_kind="file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ProvenanceError(f"cannot open model file {path.name}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        _trusted_stat(opened, f"model file {path.name}", expected_kind="file")
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ProvenanceError(f"model file changed while opening: {path.name}")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tree_sha256(records: list[dict]) -> str:
    ordered = sorted(records, key=lambda item: item["path"])
    payload = json.dumps(
        ordered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(TREE_DIGEST_PREFIX + payload).hexdigest()


def _safe_manifest_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ProvenanceError("model manifest contains an empty file path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ProvenanceError(f"unsafe model manifest path: {value!r}")
    return path.as_posix()


def _manifest_path(qwen: dict, tts_root: Path) -> Path:
    raw = qwen.get("model_file_manifest")
    if not isinstance(raw, str) or not raw.strip():
        raise ProvenanceError("Qwen model_file_manifest must be a non-empty path")
    posix = PurePosixPath(raw)
    if (
        posix.is_absolute()
        or ".." in posix.parts
        or not posix.parts
        or posix.parts[0] != MANIFEST_DIRECTORY
        or "\\" in raw
    ):
        raise ProvenanceError(
            f"Qwen model manifest must stay under {MANIFEST_DIRECTORY}/: {raw!r}"
        )
    tts_root = Path(os.path.abspath(tts_root))
    manifest_root = tts_root / MANIFEST_DIRECTORY
    path = tts_root.joinpath(*posix.parts)
    _secure_directory_tree(
        tts_root,
        path.parent,
        create=False,
        label="model manifest",
    )
    try:
        path.relative_to(manifest_root)
    except ValueError as exc:
        raise ProvenanceError("model manifest is outside the fixed manifest directory") from exc
    return path


def load_manifest(
    manifest_path: Path,
    qwen: dict,
    *,
    tts_root: Path,
) -> tuple[dict, str]:
    expected_path = _manifest_path(qwen, tts_root)
    if Path(os.path.abspath(manifest_path)) != expected_path:
        raise ProvenanceError("model manifest path does not match the pinned TTS config")
    try:
        raw, _ = _secure_read(
            expected_path,
            trusted_root=Path(os.path.abspath(tts_root)),
            label="model manifest",
        )
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"cannot read model manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ProvenanceError("model manifest must contain a JSON object")

    records = manifest.get("files")
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "tree":
        raise ProvenanceError("unsupported model manifest schema or kind")
    if manifest.get("passed") is not True or manifest.get("errors") != []:
        raise ProvenanceError("model manifest is not a passing verification record")
    if not isinstance(records, list) or not records:
        raise ProvenanceError("model manifest files must be a non-empty array")

    normalized: list[dict] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ProvenanceError("model manifest file entry is not an object")
        path = _safe_manifest_path(record.get("path"))
        size = record.get("bytes")
        digest = record.get("sha256")
        if path in seen:
            raise ProvenanceError(f"duplicate model manifest path: {path}")
        if not isinstance(size, int) or size < 0:
            raise ProvenanceError(f"invalid model manifest size: {path}")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ProvenanceError(f"invalid model manifest SHA-256: {path}")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ProvenanceError(f"invalid model manifest SHA-256: {path}") from exc
        seen.add(path)
        normalized.append({"bytes": size, "path": path, "sha256": digest.lower()})

    expected_tree = tree_sha256(normalized)
    if manifest.get("file_count") != len(normalized):
        raise ProvenanceError("model manifest file_count does not match files")
    if manifest.get("total_bytes") != sum(record["bytes"] for record in normalized):
        raise ProvenanceError("model manifest total_bytes does not match files")
    if manifest.get("sha256") != expected_tree:
        raise ProvenanceError("model manifest tree SHA-256 is internally inconsistent")
    if qwen.get("model_tree_sha256") != expected_tree:
        raise ProvenanceError("TTS config model tree SHA-256 does not match manifest")
    manifest = {**manifest, "files": sorted(normalized, key=lambda item: item["path"])}
    return manifest, hashlib.sha256(raw).hexdigest()


def model_candidates(config: dict, tts_root: Path) -> list[Path]:
    runtime = config["runtime"]
    candidates: list[Path] = []
    for env_name in runtime["qwen_base_model_envs"]:
        value = os.environ.get(env_name)
        if value:
            path = Path(value).expanduser()
            candidates.append(Path(os.path.abspath(path)))
    for value in runtime["qwen_base_model_candidates"]:
        path = Path(value)
        candidates.append(
            Path(os.path.abspath(path if path.is_absolute() else tts_root / path))
        )
    result: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        absolute = path.absolute()
        if absolute not in seen:
            result.append(absolute)
            seen.add(absolute)
    return result


def first_model_directory(config: dict, tts_root: Path) -> Path | None:
    return next((path for path in model_candidates(config, tts_root) if path.is_dir()), None)


def manifest_path(config: dict, tts_root: Path) -> Path:
    return _manifest_path(config["qwen_base"], tts_root)


def _receipt_path_for_digest(tts_root: Path, manifest_file: Path, digest: str) -> Path:
    tts_root = Path(os.path.abspath(tts_root))
    return (
        tts_root
        / RECEIPT_DIRECTORY
        / f"{manifest_file.stem}-{digest[:16]}.json"
    )


def receipt_path(config: dict, tts_root: Path) -> Path:
    source = manifest_path(config, tts_root)
    _, digest = load_manifest(
        source,
        config["qwen_base"],
        tts_root=tts_root,
    )
    return _receipt_path_for_digest(tts_root, source, digest)


def _excluded_directories(manifest: dict) -> frozenset[str]:
    values = manifest.get("excluded_directories", [])
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value and "/" not in value for value in values
    ):
        raise ProvenanceError("model manifest excluded_directories is invalid")
    return frozenset(values)


def _actual_file_map(model_root: Path, manifest: dict) -> dict[str, Path]:
    excluded = _excluded_directories(manifest)
    result: dict[str, Path] = {}
    for current, directory_names, file_names in os.walk(model_root, followlinks=False):
        current_path = Path(current)
        current_relative = current_path.relative_to(model_root)
        if current_relative.parts:
            current_stat = _lstat(current_path, f"model directory {current_relative}")
            _trusted_stat(
                current_stat,
                f"model directory {current_relative}",
                expected_kind="directory",
            )
        kept_directories: list[str] = []
        for name in directory_names:
            relative = current_relative / name
            if name in excluded:
                continue
            path = current_path / name
            directory_stat = _lstat(path, f"model directory {relative}")
            _trusted_stat(
                directory_stat,
                f"model directory {relative}",
                expected_kind="directory",
            )
            kept_directories.append(name)
        directory_names[:] = kept_directories
        for name in file_names:
            relative = current_relative / name
            if excluded.intersection(relative.parts):
                continue
            path = current_path / name
            file_stat = _lstat(path, f"model file {relative}")
            _trusted_stat(
                file_stat,
                f"model file {relative}",
                expected_kind="file",
            )
            result[relative.as_posix()] = path
    return result


def _stat_signature(path: Path, relative: str) -> dict:
    value = _lstat(path, f"model file {relative}")
    _trusted_stat(value, f"model file {relative}", expected_kind="file")
    return {
        "path": relative,
        "device": value.st_dev,
        "inode": value.st_ino,
        "bytes": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def _trusted_model_root(model_root: Path) -> Path:
    absolute = Path(os.path.abspath(model_root))
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise ProvenanceError(f"cannot resolve model root: {exc}") from exc
    if resolved != absolute:
        raise ProvenanceError("model root or one of its parents must not be a symlink")
    root_stat = _lstat(absolute, "model root")
    _trusted_stat(root_stat, "model root", expected_kind="directory")
    return absolute


def _validate_file_set(
    model_root: Path, manifest: dict
) -> tuple[dict[str, Path], dict[str, dict]]:
    actual = _actual_file_map(model_root, manifest)
    expected = {record["path"]: record for record in manifest["files"]}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        details = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if extra:
            details.append("extra=" + ", ".join(extra))
        raise ProvenanceError("model file set mismatch: " + "; ".join(details))
    signatures: dict[str, dict] = {}
    for relative, record in expected.items():
        signature = _stat_signature(actual[relative], relative)
        if signature["bytes"] != record["bytes"]:
            raise ProvenanceError(f"model size mismatch: {relative}")
        signatures[relative] = signature
    return actual, signatures


def _atomic_json(path: Path, value: dict, *, tts_root: Path) -> None:
    tts_root = Path(os.path.abspath(tts_root))
    receipt_root = _secure_directory_tree(
        tts_root,
        tts_root / RECEIPT_DIRECTORY,
        create=True,
        label="model verification receipt",
    )
    path = Path(os.path.abspath(path))
    if path.parent != receipt_root:
        raise ProvenanceError("model verification receipt is outside the fixed runtime directory")
    try:
        existing = path.lstat()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise ProvenanceError(f"cannot inspect model verification receipt: {exc}") from exc
    if existing is not None:
        if stat.S_ISLNK(existing.st_mode):
            raise ProvenanceError("model verification receipt must not be a symlink")
        _trusted_stat(
            existing,
            "model verification receipt",
            expected_kind="file",
            exact_mode=0o600,
        )
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(temporary, flags, 0o600)
    except OSError as exc:
        raise ProvenanceError(f"cannot create model verification receipt: {exc}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        final = _lstat(path, "model verification receipt")
        _trusted_stat(
            final,
            "model verification receipt",
            expected_kind="file",
            exact_mode=0o600,
        )
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _portable_claim(
    *,
    manifest: dict,
    manifest_digest: str,
    qwen: dict,
    mlx_audio_version: str,
) -> dict:
    return {
        "portable_claim_kind": PORTABLE_CLAIM_KIND,
        "verification_kind": RECEIPT_KIND,
        "model_id": qwen["model_id"],
        "model_revision": qwen["model_revision"],
        "qwen_config_sha256": canonical_sha256(qwen),
        "manifest_sha256": manifest_digest,
        "verified_model_tree_sha256": manifest["sha256"],
        "model_file_count": manifest["file_count"],
        "model_total_bytes": manifest["total_bytes"],
        "mlx_audio_version": mlx_audio_version,
    }


def _validation_summary(
    *, receipt_raw: bytes, portable_claim: dict
) -> dict:
    return {
        **portable_claim,
        "portable_claim_sha256": canonical_sha256(portable_claim),
        # The raw receipt binds the generating machine's path/inodes/stat data.
        # It is audit evidence only and deliberately excluded from the portable
        # claim used when a project is moved to another trusted workstation.
        "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
        "full_tree_hash_verified": True,
    }


def create_full_hash_receipt(
    *,
    model_root: Path,
    manifest_file: Path,
    qwen: dict,
    mlx_audio_version: str,
    tts_root: Path,
) -> dict:
    """Hash the complete model tree and atomically write a reusable receipt."""

    if mlx_audio_version != qwen.get("mlx_audio_version"):
        raise ProvenanceError(
            "mlx-audio version mismatch: "
            f"expected {qwen.get('mlx_audio_version')}, got {mlx_audio_version}"
        )
    model_root = _trusted_model_root(model_root)
    manifest, manifest_digest = load_manifest(
        manifest_file,
        qwen,
        tts_root=tts_root,
    )
    output = _receipt_path_for_digest(
        Path(os.path.abspath(tts_root)), manifest_file, manifest_digest
    )
    actual, initial_signatures = _validate_file_set(model_root, manifest)
    actual_records: list[dict] = []
    final_signatures: list[dict] = []
    for record in manifest["files"]:
        relative = record["path"]
        before = initial_signatures[relative]
        digest = sha256_file(actual[relative])
        after = _stat_signature(actual[relative], relative)
        if before != after:
            raise ProvenanceError(f"model file changed while hashing: {relative}")
        actual_records.append(
            {"bytes": after["bytes"], "path": relative, "sha256": digest}
        )
        final_signatures.append(after)

    current, current_signatures = _validate_file_set(model_root, manifest)
    if set(current) != set(actual) or any(
        current_signatures[path] != initial_signatures[path] for path in initial_signatures
    ):
        raise ProvenanceError("model tree changed while hashing")
    verified_tree = tree_sha256(actual_records)
    if verified_tree != manifest["sha256"]:
        mismatches = [
            record["path"]
            for record, actual_record in zip(manifest["files"], actual_records)
            if record["sha256"] != actual_record["sha256"]
        ]
        suffix = ": " + ", ".join(mismatches) if mismatches else ""
        raise ProvenanceError("full model tree SHA-256 mismatch" + suffix)

    portable_claim = _portable_claim(
        manifest=manifest,
        manifest_digest=manifest_digest,
        qwen=qwen,
        mlx_audio_version=mlx_audio_version,
    )
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "verification_kind": RECEIPT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": manifest_digest,
        "model_realpath": str(model_root),
        "model_id": qwen["model_id"],
        "model_revision": qwen["model_revision"],
        "qwen_config_sha256": canonical_sha256(qwen),
        "mlx_audio_version": mlx_audio_version,
        "verified_model_tree_sha256": verified_tree,
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "files": final_signatures,
        "portable_claim": portable_claim,
        "portable_claim_sha256": canonical_sha256(portable_claim),
    }
    _atomic_json(output, receipt, tts_root=tts_root)
    return receipt


def validate_receipt(
    *,
    model_root: Path,
    manifest_file: Path,
    qwen: dict,
    mlx_audio_version: str,
    tts_root: Path,
) -> dict:
    """Validate an existing full-hash receipt using cheap current stat checks."""

    if mlx_audio_version != qwen.get("mlx_audio_version"):
        raise ProvenanceError(
            "mlx-audio version mismatch: "
            f"expected {qwen.get('mlx_audio_version')}, got {mlx_audio_version}"
        )
    model_root = _trusted_model_root(model_root)
    manifest, manifest_digest = load_manifest(
        manifest_file,
        qwen,
        tts_root=tts_root,
    )
    receipt_file = _receipt_path_for_digest(
        Path(os.path.abspath(tts_root)), manifest_file, manifest_digest
    )
    try:
        raw, _ = _secure_read(
            receipt_file,
            trusted_root=Path(os.path.abspath(tts_root)),
            label="model verification receipt",
            exact_mode=0o600,
        )
        receipt = json.loads(raw.decode("utf-8"))
    except (ProvenanceError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError(
            "trusted full-model verification receipt is missing, unsafe, or unreadable "
            f"({exc}); "
            "run `python3 tools/tts/doctor.py --full-model-hash`"
        ) from exc
    if not isinstance(receipt, dict):
        raise ProvenanceError("model verification receipt must contain a JSON object")

    expected_scalars = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "verification_kind": RECEIPT_KIND,
        "manifest_sha256": manifest_digest,
        "model_realpath": str(model_root),
        "model_id": qwen["model_id"],
        "model_revision": qwen["model_revision"],
        "qwen_config_sha256": canonical_sha256(qwen),
        "mlx_audio_version": mlx_audio_version,
        "verified_model_tree_sha256": manifest["sha256"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
    }
    for key, expected in expected_scalars.items():
        if receipt.get(key) != expected:
            raise ProvenanceError(f"model verification receipt mismatch: {key}")

    portable_claim = _portable_claim(
        manifest=manifest,
        manifest_digest=manifest_digest,
        qwen=qwen,
        mlx_audio_version=mlx_audio_version,
    )
    if receipt.get("portable_claim") != portable_claim:
        raise ProvenanceError("model verification receipt mismatch: portable_claim")
    if receipt.get("portable_claim_sha256") != canonical_sha256(portable_claim):
        raise ProvenanceError("model verification receipt mismatch: portable_claim_sha256")

    actual, signatures = _validate_file_set(model_root, manifest)
    receipt_files = receipt.get("files")
    if not isinstance(receipt_files, list):
        raise ProvenanceError("model verification receipt files are invalid")
    expected_signatures = {
        record["path"]: record
        for record in receipt_files
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }
    if len(expected_signatures) != len(receipt_files) or set(expected_signatures) != set(actual):
        raise ProvenanceError("model verification receipt file set mismatch")
    for relative, signature in signatures.items():
        if expected_signatures[relative] != signature:
            raise ProvenanceError(f"model changed since full verification: {relative}")

    return _validation_summary(receipt_raw=raw, portable_claim=portable_claim)
