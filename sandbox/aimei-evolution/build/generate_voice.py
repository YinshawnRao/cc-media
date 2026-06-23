#!/usr/bin/env python3
"""Generate female narration wav files from narration.json."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
NARRATION = PROJECT / "narration.json"
VOICE_DIR = PROJECT / "audio" / "voice"
SCRIPT_DIR = PROJECT / "audio" / "voice_scripts"
OUT_JSON = PROJECT / "audio" / "voice_durations.json"


def wav_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def main() -> None:
    spec = json.loads(NARRATION.read_text(encoding="utf-8"))
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    durations = {}
    for seg in spec["segments"]:
        sid = seg["id"]
        txt = SCRIPT_DIR / f"{sid}.txt"
        wav = VOICE_DIR / f"{sid}.wav"
        txt.write_text(seg["text"], encoding="utf-8")
        cmd = [
            str(REPO / "tools/tts/venv/bin/python"),
            str(REPO / "tools/tts/narrate.py"),
            str(txt),
            "--female",
            "--speed",
            str(spec.get("speed", 1.0)),
            "-o",
            str(wav),
        ]
        subprocess.run(cmd, cwd=REPO, check=True)
        durations[sid] = round(wav_duration(wav), 3)
    OUT_JSON.write_text(json.dumps(durations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_JSON)


if __name__ == "__main__":
    main()
