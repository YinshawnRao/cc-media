#!/usr/bin/env python3
"""Fail-closed gate for one new project's resolved voice and generated sidecars."""

from __future__ import annotations

import argparse
import json
import re
import wave
from pathlib import Path

from voice_registry import VoiceRegistry, file_sha256


BYPASS_PATTERNS = {
    "direct Kokoro import": re.compile(r"(?:from\s+kokoro\s+import|import\s+kokoro)"),
    "direct KPipeline call": re.compile(r"\bKPipeline\s*\("),
    "hardcoded VOICE constant": re.compile(r"(?m)^\s*VOICE\s*="),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()

    registry = VoiceRegistry.load()
    project = args.project_root.resolve()
    selection = json.loads(args.selection.resolve().read_text(encoding="utf-8"))
    errors: list[str] = []
    if selection.get("registry_sha256") != registry.registry_sha256:
        errors.append("voice-selection.json registry hash is stale")
    if selection.get("config_sha256") != registry.config_sha256:
        errors.append("voice-selection.json config hash is stale")
    expected = selection.get("resolved_voice_id")
    if isinstance(expected, str) and expected.startswith("kokoro:"):
        legacy_voice = registry.legacy_voice(expected)
        expected_voice = None
        expected_engine = registry.config["legacy_kokoro"]["engine"]
        expected_model_id = registry.config["legacy_kokoro"]["model_id"]
        if legacy_voice is None:
            errors.append(f"voice-selection.json contains unknown legacy voice: {expected}")
    else:
        expected_voice = registry.by_id(expected or "")
        expected_engine = expected_voice.get("engine") if expected_voice else None
        expected_model_id = registry.config["qwen_base"]["model_id"]
        if expected_voice is None:
            errors.append(f"voice-selection.json contains unknown voice: {expected}")
    if selection.get("engine") != expected_engine:
        errors.append(
            f"voice-selection.json engine is {selection.get('engine')}, expected {expected_engine}"
        )

    sidecars = sorted(project.rglob("*.wav.tts.json"))
    if not sidecars:
        errors.append("no generated *.wav.tts.json sidecars found")
    for sidecar in sidecars:
        value = json.loads(sidecar.read_text(encoding="utf-8"))
        relative_sidecar = sidecar.relative_to(project)
        if value.get("resolved_voice_id") != expected:
            errors.append(
                f"{relative_sidecar} uses {value.get('resolved_voice_id')}, expected {expected}"
            )
        nested = value.get("selection", {})
        if nested != selection:
            errors.append(f"{relative_sidecar} was not generated from this project selection")
        if value.get("engine") != expected_engine:
            errors.append(
                f"{relative_sidecar} uses engine {value.get('engine')}, expected {expected_engine}"
            )
        if value.get("model_id") != expected_model_id:
            errors.append(
                f"{relative_sidecar} uses model {value.get('model_id')}, expected {expected_model_id}"
            )
        if expected_voice is not None:
            qwen = registry.config["qwen_base"]
            if value.get("model_revision") != qwen["model_revision"]:
                errors.append(f"{relative_sidecar} has the wrong Qwen model revision")
            if value.get("model_tree_sha256") != qwen["model_tree_sha256"]:
                errors.append(f"{relative_sidecar} has the wrong Qwen model tree hash")
            if value.get("reference_sha256") != expected_voice["reference_sha256"]:
                errors.append(f"{relative_sidecar} has the wrong reference-audio hash")

        output_value = value.get("output")
        output = Path(output_value) if isinstance(output_value, str) else Path("")
        try:
            output.resolve().relative_to(project)
        except ValueError:
            errors.append(f"{relative_sidecar} points outside the project: {output}")
            continue
        if not output.is_file():
            errors.append(f"{relative_sidecar} points to missing WAV: {output}")
            continue
        if value.get("output_sha256") != file_sha256(output):
            errors.append(f"{relative_sidecar} output WAV hash does not match")
        try:
            with wave.open(str(output), "rb") as handle:
                if handle.getnchannels() != 1 or handle.getframerate() != 24000:
                    errors.append(f"{relative_sidecar} output is not 24kHz mono WAV")
                if handle.getnframes() <= 0:
                    errors.append(f"{relative_sidecar} output WAV is empty")
        except (OSError, wave.Error) as exc:
            errors.append(f"{relative_sidecar} output is not a readable WAV: {exc}")

    excluded_parts = {"archive", ".deps", "node_modules", "venv", "qwen.venv"}
    for source in sorted(project.rglob("*.py")):
        if excluded_parts.intersection(source.parts):
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for label, pattern in BYPASS_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{source.relative_to(project)} bypasses central TTS: {label}")

    if errors:
        print("VOICE GATE: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VOICE GATE: PASS  voice={expected}  sidecars={len(sidecars)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
