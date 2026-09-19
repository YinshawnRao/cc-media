#!/usr/bin/env python3
"""Run the shared offline generator with this lab's isolated roots."""

from __future__ import annotations

import importlib.util
from pathlib import Path


LAB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_ROOT.parents[3]
SHARED = (
    REPO_ROOT
    / "tools"
    / "tts"
    / "research"
    / "qwen-voice-expansion-lab"
    / "src"
    / "generate_samples.py"
)


def main() -> int:
    research_root = (REPO_ROOT / "tools" / "tts" / "research").resolve()
    if research_root not in LAB_ROOT.resolve().parents:
        raise SystemExit("refusing to run outside tools/tts/research")
    spec = importlib.util.spec_from_file_location("qwen_voice_lab_generator", SHARED)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load shared generator: {SHARED}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.LAB_ROOT = LAB_ROOT
    module.REPO_ROOT = REPO_ROOT
    module.MANIFEST_PATH = LAB_ROOT / "manifest.json"
    module.OUTPUT_ROOT = LAB_ROOT / "outputs"
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
