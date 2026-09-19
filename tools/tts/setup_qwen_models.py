#!/usr/bin/env python3
"""Install or verify pinned Qwen weights inside cc-media (no cross-repo fallback)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parent
MODELS = {
    "base": "qwen-base-8bit.json",
    "voice-design": "qwen-voicedesign-8bit.json",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_files(root: Path, manifest: dict) -> list[str]:
    errors = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.resolve().is_relative_to(root.resolve()):
            errors.append(f"outside model directory: {record['path']}")
        elif not path.is_file():
            errors.append(f"missing: {record['path']}")
        elif path.stat().st_size != record["bytes"] or file_sha256(path) != record["sha256"]:
            errors.append(f"checksum mismatch: {record['path']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=(*MODELS, "all"), default="all")
    parser.add_argument("--verify-only", action="store_true", help="read local files only; never download")
    args = parser.parse_args()
    selected = MODELS if args.model == "all" else {args.model: MODELS[args.model]}
    for name, filename in selected.items():
        manifest = json.loads((TTS_ROOT / "model-manifests" / filename).read_text())
        root = TTS_ROOT / manifest["source"]
        if not root.resolve().is_relative_to(TTS_ROOT / "models"):
            raise SystemExit("model destination must stay inside tools/tts/models")
        errors = verify_files(root, manifest)
        if any(error.startswith("outside model directory:") for error in errors):
            raise SystemExit("QWEN MODEL FILES: FAIL\n" + "\n".join(errors))
        if errors and not args.verify_only:
            # Public weights only. Keep download/cache files in this repository,
            # and use the recorded immutable revision, never a moving branch.
            runtime = TTS_ROOT / "runtime" / "model-downloads"
            os.environ["HF_HOME"] = str(runtime / "hf")
            os.environ["HF_XET_CACHE"] = str(runtime / "xet")
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            from huggingface_hub import snapshot_download

            model_name, revision = root.name.rsplit("@", 1)
            print(f"Downloading {name} into {root}", flush=True)
            snapshot_download(
                repo_id=f"mlx-community/{model_name}",
                revision=revision,
                local_dir=root,
                cache_dir=runtime / "hf" / "hub",
                allow_patterns=[record["path"] for record in manifest["files"]],
                token=False,
                max_workers=4,
                force_download=any(error.startswith("checksum mismatch:") for error in errors),
            )
            errors = verify_files(root, manifest)
        if errors:
            raise SystemExit(f"QWEN MODEL FILES: FAIL {name}\n" + "\n".join(errors))
        print(
            f"QWEN MODEL FILES: PASS {name} files={manifest['file_count']} "
            f"bytes={manifest['total_bytes']} all_sha256=verified path={root}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
