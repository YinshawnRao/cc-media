#!/usr/bin/env python3
"""Transcribe production-like samples with the existing local Whisper small model."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parents[3]
DEFAULT_MODEL = "small"
OBSERVED_TRADITIONAL_TO_SIMPLIFIED = str.maketrans(
    {
        "讓": "让",
        "記": "记",
        "間": "间",
        "滿": "满",
        "緒": "绪",
        "準": "准",
        "備": "备",
        "戲": "戏",
        "剛": "刚",
        "開": "开",
    }
)


def normalize(text: str) -> str:
    # Whisper may emit Traditional characters for otherwise identical Mandarin.
    # Preserve the raw transcript in the report and normalize only observed
    # script variants for the mechanical similarity score.
    text = text.translate(OBSERVED_TRADITIONAL_TO_SIMPLIFIED)
    return re.sub(r"[^0-9a-z\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]+", "", text.lower())


def similarity(expected: str, actual: str) -> float:
    return difflib.SequenceMatcher(a=normalize(expected), b=normalize(actual)).ratio()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, help="debug: only process N files")
    args = parser.parse_args()

    import whisper

    manifest = json.loads((EXPERIMENT_ROOT / "manifest.json").read_text(encoding="utf-8"))
    listen_root = EXPERIMENT_ROOT / "outputs" / "listen-audio"
    jobs = []
    for persona in manifest["personas"]:
        for text_id in ("showcase", "mixed_language"):
            path = listen_root / "qwen3-tts" / persona["id"] / f"{text_id}.wav"
            if path.is_file():
                jobs.append(
                    {
                        "engine": "qwen3-tts",
                        "voice": persona["id"],
                        "text_id": text_id,
                        "expected": manifest["texts"][text_id],
                        "path": path,
                    }
                )
    for voice in manifest["kokoro_voices"]:
        path = listen_root / "kokoro" / f"{voice}.wav"
        if path.is_file():
            jobs.append(
                {
                    "engine": "kokoro",
                    "voice": voice,
                    "text_id": "showcase",
                    "expected": manifest["texts"]["showcase"],
                    "path": path,
                }
            )
    if args.limit:
        jobs = jobs[: args.limit]
    if not jobs:
        raise SystemExit("no listening WAVs found; run prepare_listen_audio.py first")

    print(f"loading local Whisper {args.model} on CPU", flush=True)
    started = time.perf_counter()
    model = whisper.load_model(args.model, device="cpu")
    load_seconds = time.perf_counter() - started
    records = []
    for index, job in enumerate(jobs, 1):
        print(f"[{index}/{len(jobs)}] {job['engine']} {job['voice']} {job['text_id']}", flush=True)
        started = time.perf_counter()
        result = model.transcribe(
            str(job["path"]),
            language="zh",
            task="transcribe",
            fp16=False,
            verbose=False,
            condition_on_previous_text=False,
        )
        actual = result.get("text", "").strip()
        score = similarity(job["expected"], actual)
        records.append(
            {
                "engine": job["engine"],
                "voice": job["voice"],
                "text_id": job["text_id"],
                "path": str(job["path"].relative_to(EXPERIMENT_ROOT)),
                "expected": job["expected"],
                "transcript": actual,
                "normalized_similarity": score,
                "elapsed_seconds": time.perf_counter() - started,
                "interpretation": (
                    "content_check"
                    if job["text_id"] == "showcase"
                    else "mixed-script evidence only; ASR spelling is not a pronunciation verdict"
                ),
            }
        )

    report = {
        "schema_version": "1.0.0",
        "model": args.model,
        "device": "cpu",
        "load_seconds": load_seconds,
        "python": sys.version.split()[0],
        "records": records,
        "summary": {
            "total": len(records),
            "showcase_below_0_85": sum(
                row["text_id"] == "showcase" and row["normalized_similarity"] < 0.85
                for row in records
            ),
            "showcase_min_similarity": min(
                (
                    row["normalized_similarity"]
                    for row in records
                    if row["text_id"] == "showcase"
                ),
                default=None,
            ),
        },
    }
    output = EXPERIMENT_ROOT / "qa" / "asr-report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
