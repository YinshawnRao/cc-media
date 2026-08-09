#!/usr/bin/env python3
"""Probe every generated WAV and write machine-readable technical QA evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = EXPERIMENT_ROOT / "outputs"
QA_ROOT = EXPERIMENT_ROOT / "qa"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def parse_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    value = match.group(1)
    if value == "-inf":
        return None
    return float(value)


def probe(path: Path) -> dict:
    ffprobe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,codec_type,sample_rate,channels,channel_layout,bits_per_sample",
            "-of",
            "json",
            str(path),
        ]
    )
    volume = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    silence = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "silencedetect=n=-45dB:d=0.8",
            "-f",
            "null",
            "-",
        ]
    )
    errors = []
    info = {}
    if ffprobe.returncode:
        errors.append("ffprobe_failed")
    else:
        info = json.loads(ffprobe.stdout)
    if volume.returncode:
        errors.append("volumedetect_failed")
    if silence.returncode:
        errors.append("silencedetect_failed")

    streams = info.get("streams", [])
    stream = streams[0] if streams else {}
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    mean_volume = parse_float(r"mean_volume:\s+(-?inf|-?\d+(?:\.\d+)?) dB", volume.stderr)
    max_volume = parse_float(r"max_volume:\s+(-?inf|-?\d+(?:\.\d+)?) dB", volume.stderr)
    silence_durations = [
        float(value)
        for value in re.findall(r"silence_duration:\s*(\d+(?:\.\d+)?)", silence.stderr)
    ]
    warnings = []
    if duration < 1.0:
        errors.append("duration_too_short")
    if max_volume is not None and max_volume >= -0.05:
        warnings.append("peak_near_0dbfs_check_for_clipping")
    if silence_durations:
        warnings.append("contains_silence_over_0.8s")
    return {
        "path": str(path.relative_to(EXPERIMENT_ROOT)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "duration_seconds": duration,
        "codec": stream.get("codec_name"),
        "sample_rate_hz": int(stream.get("sample_rate", 0) or 0),
        "channels": stream.get("channels"),
        "channel_layout": stream.get("channel_layout"),
        "bits_per_sample": stream.get("bits_per_sample"),
        "mean_volume_db": mean_volume,
        "max_volume_db": max_volume,
        "silence_durations_over_0_8s": silence_durations,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    files = sorted(OUTPUT_ROOT.rglob("*.wav"))
    if not files:
        raise SystemExit("no WAV files found; run the generators first")
    records = []
    for index, path in enumerate(files, 1):
        print(f"[{index}/{len(files)}] {path.relative_to(EXPERIMENT_ROOT)}")
        records.append(probe(path))

    QA_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0.0",
        "files": records,
        "summary": {
            "total": len(records),
            "passed": sum(item["status"] == "PASS" for item in records),
            "failed": sum(item["status"] == "FAIL" for item in records),
            "warnings": sum(bool(item["warnings"]) for item in records),
        },
    }
    (QA_ROOT / "audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    columns = [
        "path",
        "status",
        "duration_seconds",
        "sample_rate_hz",
        "channels",
        "mean_volume_db",
        "max_volume_db",
        "warnings",
        "sha256",
    ]
    with (QA_ROOT / "audio-summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for item in records:
            row = {key: item.get(key) for key in columns}
            row["warnings"] = ";".join(item["warnings"])
            writer.writerow(row)
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
