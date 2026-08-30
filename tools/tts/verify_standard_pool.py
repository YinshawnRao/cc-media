#!/usr/bin/env python3
"""Generate and verify one production-path sample for every standard-pool voice."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from voice_registry import VoiceRegistry


TTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TTS_ROOT.parents[1]
VOICE_ROOT = TTS_ROOT / "voices"
RESOURCE_BUDGET = REPO_ROOT / "tools" / "video" / "resource_budget.py"
OFFLINE_ASR = REPO_ROOT / "tools" / "video" / "offline_asr.py"
THREAD_TOKEN = "__CC_MEDIA_THREADS__"
SMOKE_TEXT = "这是标准配音生产链路稳定性检查。声音应该自然清楚，没有杂音，也不会异常拖长。"
TRADITIONAL_FOLD = str.maketrans(
    {
        "這": "这",
        "標": "标",
        "準": "准",
        "產": "产",
        "煉": "链",
        "穩": "稳",
        "檢": "检",
        "聲": "声",
        "應": "应",
        "該": "该",
        "沒": "没",
        "雜": "杂",
        "會": "会",
        "場": "场",
        "長": "长",
    }
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    command: list[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match or match.group(1) == "-inf":
        return None
    return float(match.group(1))


def probe_audio(path: Path) -> dict:
    ffprobe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,sample_rate,channels,bits_per_sample",
            "-of",
            "json",
            str(path),
        ]
    )
    analysis = run(
        [
            sys.executable,
            str(RESOURCE_BUDGET),
            "ffmpeg",
            "--",
            "ffmpeg",
            "-threads",
            THREAD_TOKEN,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "silencedetect=n=-45dB:d=1.5,volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    errors: list[str] = []
    info: dict = {}
    if ffprobe.returncode:
        errors.append("ffprobe_failed")
    else:
        try:
            info = json.loads(ffprobe.stdout)
        except json.JSONDecodeError:
            errors.append("ffprobe_invalid_json")
    if analysis.returncode:
        errors.append("ffmpeg_analysis_failed")
    stream = (info.get("streams") or [{}])[0]
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    mean_volume = parse_float(
        r"mean_volume:\s+(-?inf|-?\d+(?:\.\d+)?) dB", analysis.stderr
    )
    max_volume = parse_float(
        r"max_volume:\s+(-?inf|-?\d+(?:\.\d+)?) dB", analysis.stderr
    )
    silences = [
        float(value)
        for value in re.findall(r"silence_duration:\s*(\d+(?:\.\d+)?)", analysis.stderr)
    ]
    if not 1.0 <= duration <= 20.0:
        errors.append("duration_out_of_range")
    if stream.get("codec_name") != "pcm_s16le":
        errors.append("codec_not_pcm_s16le")
    if int(stream.get("sample_rate", 0) or 0) != 24000:
        errors.append("sample_rate_not_24000")
    if stream.get("channels") != 1:
        errors.append("not_mono")
    if mean_volume is None or not -36.0 <= mean_volume <= -5.0:
        errors.append("mean_volume_out_of_range")
    if max_volume is None or max_volume >= -0.05:
        errors.append("peak_clipping_or_unavailable")
    if silences:
        errors.append("contains_silence_over_1_5s")
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "duration_seconds": duration,
        "codec": stream.get("codec_name"),
        "sample_rate_hz": int(stream.get("sample_rate", 0) or 0),
        "channels": stream.get("channels"),
        "bits_per_sample": stream.get("bits_per_sample"),
        "mean_volume_db": mean_volume,
        "max_volume_db": max_volume,
        "silence_durations_over_1_5s": silences,
        "errors": errors,
    }


def normalized_text(value: str) -> str:
    folded = value.translate(TRADITIONAL_FOLD)
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", folded, flags=re.UNICODE).lower()


def asr_python() -> Path:
    override = os.environ.get("CC_MEDIA_ASR_PYTHON")
    candidate = Path(override).expanduser() if override else TTS_ROOT / "venv" / "bin" / "python"
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise RuntimeError("fixed offline-ASR Python is unavailable")
    # Keep the venv launcher path intact. Resolving its symlink would invoke the
    # base interpreter and lose the pinned openai-whisper distribution metadata.
    return Path(os.path.abspath(candidate))


def run_asr(samples: dict[str, Path]) -> dict[str, dict]:
    request = {
        "model": "small",
        "language": "zh",
        "jobs": [
            {"id": voice_id, "path": str(path.resolve())}
            for voice_id, path in samples.items()
        ],
    }
    completed = run(
        [str(asr_python()), str(OFFLINE_ASR)],
        input_text=json.dumps(request, ensure_ascii=False),
    )
    if completed.returncode:
        raise RuntimeError(f"offline ASR failed: {completed.stderr.strip()}")
    payload = json.loads(completed.stdout)
    expected = normalized_text(SMOKE_TEXT)
    results: dict[str, dict] = {}
    for item in payload["results"]:
        observed = str(item.get("transcript", "")).strip()
        ratio = difflib.SequenceMatcher(
            None, expected, normalized_text(observed)
        ).ratio()
        results[item["source_id"]] = {
            "transcript": observed,
            "similarity": round(ratio, 6),
            "errors": [] if ratio >= 0.55 else ["asr_similarity_below_0_55"],
        }
    for voice_id in samples:
        if voice_id not in results:
            results[voice_id] = {
                "transcript": "",
                "similarity": 0.0,
                "errors": ["asr_result_missing"],
            }
    return results


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=VOICE_ROOT / "standard-pool-smoke.json",
        help="write the hash-bound smoke report",
    )
    parser.add_argument(
        "--skip-asr",
        action="store_true",
        help="diagnostic only: skip the required intelligibility check",
    )
    args = parser.parse_args(argv)
    registry = VoiceRegistry.load()
    results: list[dict] = []
    sample_paths: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="cc-media-standard-pool-") as temporary:
        # macOS exposes /var as a symlink to /private/var. The production voice
        # gate intentionally rejects symlinked project ancestors, so canonicalize
        # only this disposable root before creating the synthetic projects.
        root = Path(temporary).resolve()
        for index, voice in enumerate(registry.decision_pool, 1):
            voice_id = voice["id"]
            project = root / voice_id
            project.mkdir()
            output = project / "smoke.wav"
            selection = project / "voice-selection.json"
            print(
                f"STANDARD POOL {index:02d}/{len(registry.decision_pool):02d} {voice_id} generate",
                flush=True,
            )
            generation = run(
                [
                    sys.executable,
                    str(TTS_ROOT / "narrate.py"),
                    SMOKE_TEXT,
                    "--voice",
                    voice_id,
                    "--selection-output",
                    str(selection),
                    "--output",
                    str(output),
                    "--force",
                ]
            )
            errors: list[str] = []
            if generation.returncode:
                errors.append("production_generation_failed")
            voice_gate = None
            audio = None
            if not errors:
                gate = run(
                    [
                        sys.executable,
                        str(TTS_ROOT / "verify_voice_usage.py"),
                        "--selection",
                        str(selection),
                        "--project-root",
                        str(project),
                    ]
                )
                voice_gate = gate.stdout.strip()
                if gate.returncode or "VOICE GATE: PASS" not in gate.stdout:
                    errors.append("voice_gate_failed")
                try:
                    audio = probe_audio(output)
                    errors.extend(audio["errors"])
                except (OSError, ValueError, json.JSONDecodeError):
                    errors.append("audio_probe_failed")
            if output.is_file():
                sample_paths[voice_id] = output
            results.append(
                {
                    "voice_id": voice_id,
                    "voice_name": voice["name"],
                    "reference_sha256": voice["reference_sha256"],
                    "reference_text_sha256": hashlib.sha256(
                        registry.reference_text_for(voice).encode("utf-8")
                    ).hexdigest(),
                    "generation_returncode": generation.returncode,
                    "generation_stdout": (
                        generation.stdout.strip() if generation.returncode else ""
                    ),
                    "generation_stderr": (
                        generation.stderr.strip() if generation.returncode else ""
                    ),
                    "voice_gate": voice_gate,
                    "audio": audio,
                    "errors": errors,
                }
            )

        asr_results: dict[str, dict] = {}
        if not args.skip_asr and len(sample_paths) == len(registry.decision_pool):
            print("STANDARD POOL ASR verify", flush=True)
            try:
                asr_results = run_asr(sample_paths)
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                asr_results = {
                    voice_id: {"transcript": "", "similarity": 0.0, "errors": [str(exc)]}
                    for voice_id in sample_paths
                }
            for item in results:
                asr = asr_results.get(item["voice_id"])
                item["asr"] = asr
                if asr:
                    item["errors"].extend(asr["errors"])
        elif args.skip_asr:
            for item in results:
                item["asr"] = {"status": "SKIP", "errors": []}

    failures = [item["voice_id"] for item in results if item["errors"]]
    report = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": registry.config_sha256,
        "registry_sha256": registry.registry_sha256,
        "standard_voice_ids": registry.decision_pool_ids,
        "smoke_text": SMOKE_TEXT,
        "asr_required": not args.skip_asr,
        "status": "PASS" if not failures else "FAIL",
        "summary": {
            "total": len(results),
            "passed": len(results) - len(failures),
            "failed": len(failures),
            "failed_voice_ids": failures,
        },
        "voices": results,
    }
    write_report(args.report.resolve(), report)
    if failures:
        print(
            f"STANDARD POOL SMOKE: FAIL failed={','.join(failures)} report={args.report}",
            flush=True,
        )
        return 1
    print(
        f"STANDARD POOL SMOKE: PASS voices={len(results)} report={args.report}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
