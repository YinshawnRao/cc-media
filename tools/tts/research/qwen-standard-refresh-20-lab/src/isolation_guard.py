#!/usr/bin/env python3
"""Snapshot and verify that isolated generation did not mutate formal TTS assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


LAB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_ROOT.parents[3]
OUTPUT_ROOT = LAB_ROOT / "outputs"
QA_ROOT = OUTPUT_ROOT / "qa"
BEFORE_PATH = QA_ROOT / "isolation-before.json"
AFTER_PATH = QA_ROOT / "isolation-after.json"
REPORT_PATH = QA_ROOT / "isolation-report.json"
PROTECTED = [
    "tools/tts/config.json",
    "tools/tts/narrate.py",
    "tools/tts/resolve_voice.py",
    "tools/tts/verify_voice_usage.py",
    "tools/tts/voice_registry.py",
    "tools/tts/qwen_contract.py",
    "tools/tts/engines",
    "tools/tts/voices",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_boundary() -> dict:
    research_root = (REPO_ROOT / "tools" / "tts" / "research").resolve()
    lab = LAB_ROOT.resolve()
    output = OUTPUT_ROOT.resolve()
    manifest = json.loads((LAB_ROOT / "manifest.json").read_text(encoding="utf-8"))
    isolation = manifest.get("isolation", {})
    errors = []
    if research_root not in lab.parents:
        errors.append("lab_outside_research_root")
    if lab not in output.parents:
        errors.append("output_outside_lab")
    if isolation.get("formal_tts_read_only") is not True:
        errors.append("formal_tts_read_only_not_true")
    if isolation.get("promote_automatically") is not False:
        errors.append("promote_automatically_not_false")
    if isolation.get("output_root") != "outputs":
        errors.append("unexpected_output_root")
    counts = {
        group: sum(persona.get("group") == group for persona in manifest.get("personas", []))
        for group in ("female", "male")
    }
    if counts != isolation.get("expected_groups"):
        errors.append(f"unexpected_group_counts:{counts}")
    if errors:
        raise SystemExit("ISOLATION GATE: FAIL — " + ", ".join(errors))
    return {"lab_root": str(lab.relative_to(REPO_ROOT)), "output_root": str(output.relative_to(REPO_ROOT)), "group_counts": counts}


def snapshot() -> dict:
    boundary = validate_boundary()
    files = {}
    for relative in PROTECTED:
        target = REPO_ROOT / relative
        paths = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
        for path in paths:
            files[str(path.relative_to(REPO_ROOT))] = sha256(path)
    return {"schema_version": "1.0.0", "boundary": boundary, "files": files}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "verify"))
    args = parser.parse_args()
    current = snapshot()
    if args.mode == "capture":
        write_json(BEFORE_PATH, current)
        print(f"ISOLATION SNAPSHOT: PASS files={len(current['files'])} path={BEFORE_PATH}")
        return 0
    if not BEFORE_PATH.is_file():
        raise SystemExit("ISOLATION GATE: FAIL — missing capture snapshot")
    before = json.loads(BEFORE_PATH.read_text(encoding="utf-8"))
    before_files = before.get("files", {})
    after_files = current["files"]
    changed = sorted(path for path in set(before_files) | set(after_files) if before_files.get(path) != after_files.get(path))
    write_json(AFTER_PATH, current)
    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if not changed else "FAIL",
        "protected_file_count": len(after_files),
        "changed_files": changed,
        "before_snapshot": str(BEFORE_PATH.relative_to(LAB_ROOT)),
        "after_snapshot": str(AFTER_PATH.relative_to(LAB_ROOT)),
    }
    write_json(REPORT_PATH, report)
    if changed:
        raise SystemExit("ISOLATION GATE: FAIL — protected files changed: " + ", ".join(changed))
    print(f"ISOLATION GATE: PASS protected_files={len(after_files)} changed=0 path={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
