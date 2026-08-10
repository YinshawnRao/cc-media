#!/usr/bin/env python3
"""Assemble a long-form timeline's frozen footage spine and master audio.

Inputs are project-local, already selected/verticalized clips and pre-mixed WAV
segments. The script deliberately leaves cover/HTML design to the project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, NoReturn


KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROLES = {"intro", "song", "outro", "cta", "free"}
ACCEPTANCE = {"showcase_align", "instrumental_plan", "not_applicable"}
AUDIO_DURATION_TOLERANCE_SECONDS = 0.05


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def resolve_inside(root: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        fail(f"{label} must be a non-empty project-relative path")
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        fail(f"{label} must stay inside the project: {raw!r}")
    root = root.resolve()
    logical = root / candidate
    resolved = logical.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        fail(f"{label} resolves outside the project: {raw!r}")
    # Preserve the logical path so output checks can reject symlink parents.
    return logical


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sidecar_path(project: Path, voice: Path) -> Path:
    """Resolve a TTS sidecar without following a project-external symlink."""
    project = project.resolve()
    logical = Path(f"{voice}.tts.json")
    try:
        relative = logical.relative_to(project)
    except ValueError:
        fail(f"TTS sidecar logical path is outside the project: {logical}")
    cursor = project
    for part in relative.parent.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"TTS sidecar parent must not be a symlink: {cursor}")
    if logical.is_symlink():
        fail(f"TTS sidecar must not be a symlink: {logical}")
    try:
        logical.resolve().relative_to(project)
    except ValueError:
        fail(f"TTS sidecar resolves outside the project: {logical}")
    return logical


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"config not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(value, dict):
        fail("config root must be an object")
    return value


def require_tools() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        fail(f"missing required command(s): {', '.join(missing)}")


def run(command: list[str], label: str, cwd: Path) -> None:
    print(f"[run] {label}")
    subprocess.run(command, cwd=cwd, check=True)


def probe(path: Path, entries: str, stream: str | None = None) -> dict[str, Any]:
    command = ["ffprobe", "-v", "error"]
    if stream:
        command += ["-select_streams", stream]
    command += ["-show_entries", entries, "-of", "json", str(path)]
    return json.loads(subprocess.check_output(command, text=True))


def media_duration(path: Path) -> float:
    return float(probe(path, "format=duration")["format"]["duration"])


def parse_config(project: Path, raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schema_version") != 1:
        fail("unsupported schema_version; expected 1")
    selection = resolve_inside(project, raw.get("voice_selection"), "voice_selection")
    if "narration_wavs" in raw:
        fail("top-level narration_wavs is not supported; bind narration_wavs to each segment")

    outputs_raw = raw.get("outputs")
    if not isinstance(outputs_raw, dict):
        fail("outputs must be an object")
    outputs = {
        name: resolve_inside(project, outputs_raw.get(name), f"outputs.{name}")
        for name in ("master_audio", "footage_track", "timeline")
    }
    if len(set(outputs.values())) != len(outputs):
        fail("master_audio, footage_track and timeline outputs must be distinct")

    video = raw.get("video")
    if not isinstance(video, dict):
        fail("video must be an object")
    width, height, fps = video.get("width"), video.get("height"), video.get("fps")
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in (width, height, fps)):
        fail("video width, height and fps must be positive integers")

    rows = raw.get("segments")
    if not isinstance(rows, list) or not rows:
        fail("segments must be a non-empty array")
    segments: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        label = f"segments[{index}]"
        if not isinstance(row, dict):
            fail(f"{label} must be an object")
        key = row.get("key")
        role = row.get("role")
        if not isinstance(key, str) or not KEY_RE.fullmatch(key):
            fail(f"{label}.key must match {KEY_RE.pattern}")
        if key in seen:
            fail(f"duplicate segment key: {key}")
        seen.add(key)
        if role not in ROLES:
            fail(f"{label}.role must be one of {sorted(ROLES)}")
        seek = row.get("source_seek_sec", 0.0)
        duration = row.get("duration_sec")
        if not isinstance(seek, (int, float)) or isinstance(seek, bool) or seek < 0:
            fail(f"{label}.source_seek_sec must be >= 0")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            fail(f"{label}.duration_sec must be > 0")
        acceptance = row.get("acceptance", "not_applicable")
        if acceptance not in ACCEPTANCE:
            fail(f"{label}.acceptance must be one of {sorted(ACCEPTANCE)}")
        if role == "song" and acceptance == "not_applicable":
            fail(f"{label} song segment requires showcase_align or instrumental_plan acceptance")
        narration_raw = row.get("narration_wavs")
        if not isinstance(narration_raw, list):
            fail(f"{label}.narration_wavs must be an explicit array")
        if role != "free" and not narration_raw:
            fail(f"{label}.narration_wavs must bind at least one TTS WAV for role {role}")
        narration = [
            resolve_inside(project, value, f"{label}.narration_wavs[{voice_index}]")
            for voice_index, value in enumerate(narration_raw)
        ]
        if len(set(narration)) != len(narration):
            fail(f"{label}.narration_wavs must not contain duplicates")
        audio_segment_sha256 = row.get("audio_segment_sha256")
        if not isinstance(audio_segment_sha256, str) or not SHA256_RE.fullmatch(
            audio_segment_sha256
        ):
            fail(f"{label}.audio_segment_sha256 must be 64 lowercase hex characters")
        segments.append(
            {
                "key": key,
                "role": role,
                "clip": resolve_inside(project, row.get("clip"), f"{label}.clip"),
                "audio_segment": resolve_inside(
                    project, row.get("audio_segment"), f"{label}.audio_segment"
                ),
                "audio_segment_sha256": audio_segment_sha256,
                "narration_wavs": narration,
                "source_seek_sec": float(seek),
                "duration_sec": float(duration),
                "acceptance": acceptance,
            }
        )

    return {
        "selection": selection,
        "outputs": outputs,
        "video": {"width": width, "height": height, "fps": fps},
        "segments": segments,
    }


def validate_inputs(config: dict[str, Any], project: Path) -> None:
    missing: list[Path] = []
    sidecars: dict[Path, Path] = {}
    if not config["selection"].is_file():
        missing.append(config["selection"])
    for segment in config["segments"]:
        for voice in segment["narration_wavs"]:
            if not voice.is_file():
                missing.append(voice)
            sidecar = sidecar_path(project, voice)
            sidecars[voice] = sidecar
            if not sidecar.is_file():
                missing.append(sidecar)
        for path in (segment["clip"], segment["audio_segment"]):
            if not path.is_file():
                missing.append(path)
    if missing:
        rendered = "\n".join(f"  - {path}" for path in missing)
        fail(f"missing required project inputs:\n{rendered}")

    selection = load_json(config["selection"])
    expected_voice = selection.get("resolved_voice_id")
    if not isinstance(expected_voice, str) or not expected_voice.strip():
        fail("voice-selection.json resolved_voice_id must be non-empty")

    width = config["video"]["width"]
    height = config["video"]["height"]
    for segment in config["segments"]:
        key = segment["key"]
        for voice in segment["narration_wavs"]:
            sidecar = load_json(sidecars[voice])
            if sidecar.get("selection") != selection:
                fail(
                    f"{key} narration sidecar selection does not match "
                    f"voice-selection.json: {voice}"
                )
            if sidecar.get("resolved_voice_id") != expected_voice:
                fail(f"{key} narration sidecar resolved voice does not match project: {voice}")
            if sidecar.get("output_sha256") != sha256_file(voice):
                fail(f"{key} narration sidecar output hash does not match WAV: {voice}")

        actual_audio_sha256 = sha256_file(segment["audio_segment"])
        if actual_audio_sha256 != segment["audio_segment_sha256"]:
            fail(
                f"{key} audio_segment SHA-256 mismatch: expected "
                f"{segment['audio_segment_sha256']}, got {actual_audio_sha256}"
            )
        stream = probe(segment["clip"], "stream=width,height", "v:0")["streams"][0]
        actual = (int(stream["width"]), int(stream["height"]))
        if actual != (width, height):
            fail(
                f"{segment['key']} clip is {actual[0]}x{actual[1]}, expected "
                f"{width}x{height}; run vfill first"
            )
        available = media_duration(segment["clip"]) - segment["source_seek_sec"]
        if available + 0.05 < segment["duration_sec"]:
            fail(f"{key} clip is too short for the configured window")
        audio_duration = media_duration(segment["audio_segment"])
        if audio_duration + AUDIO_DURATION_TOLERANCE_SECONDS < segment["duration_sec"]:
            fail(
                f"{key} audio_segment is {audio_duration:.3f}s but duration_sec is "
                f"{segment['duration_sec']:.3f}s; pre-mix the complete segment instead of padding"
            )


def concat_list_line(path: Path) -> str:
    escaped = path.name.replace("'", "'\\''")
    return f"file '{escaped}'\n"


def ensure_safe_output(project: Path, output: Path) -> None:
    project = project.resolve()
    try:
        relative = output.relative_to(project)
    except ValueError:
        fail(f"output is outside the project: {output}")
    cursor = project
    for part in relative.parent.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"output parent must not be a symlink: {cursor}")
    if output.is_symlink():
        fail(f"output file must not be a symlink: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.parent.resolve().relative_to(project)
    except ValueError:
        fail(f"output parent escaped the project: {output.parent}")


def ensure_safe_directory(project: Path, directory: Path) -> None:
    ensure_safe_output(project, directory / ".write-check")


def build(config: dict[str, Any], project: Path) -> None:
    temporary = resolve_inside(project, "tmp/longform-timeline", "temporary directory")
    ensure_safe_directory(project, temporary)
    video_dir = temporary / "video"
    audio_dir = temporary / "audio"
    ensure_safe_directory(project, video_dir)
    ensure_safe_directory(project, audio_dir)

    timeline_segments: list[dict[str, Any]] = []
    video_parts: list[Path] = []
    audio_parts: list[Path] = []
    cursor = 0.0
    video = config["video"]
    selection = load_json(config["selection"])
    resolved_voice_id = selection["resolved_voice_id"]

    for index, segment in enumerate(config["segments"]):
        key = segment["key"]
        duration = segment["duration_sec"]
        audio_duration = media_duration(segment["audio_segment"])
        if audio_duration + AUDIO_DURATION_TOLERANCE_SECONDS < duration:
            fail(
                f"{key} audio_segment became too short after validation; "
                "refusing to synthesize a long padded track"
            )
        video_part = video_dir / f"{index:03d}-{key}.mp4"
        audio_part = audio_dir / f"{index:03d}-{key}.wav"
        ensure_safe_output(project, video_part)
        ensure_safe_output(project, audio_part)
        run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(segment["clip"]),
                "-ss", f"{segment['source_seek_sec']:.3f}", "-t", f"{duration:.3f}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", str(video["fps"]), "-g", str(video["fps"]),
                "-keyint_min", str(video["fps"]), "-movflags", "+faststart",
                str(video_part),
            ],
            f"precut footage {key}",
            project,
        )
        run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(segment["audio_segment"]),
                # Validation permits only a <=50 ms container/encoding gap.
                # whole_dur can fill that tiny gap, never missing content.
                "-af", f"atrim=0:{duration:.3f},apad=whole_dur={duration:.3f}",
                "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(audio_part),
            ],
            f"normalize audio segment {key}",
            project,
        )
        video_parts.append(video_part)
        audio_parts.append(audio_part)
        timeline_segments.append(
            {
                "key": key,
                "role": segment["role"],
                "start_sec": round(cursor, 3),
                "end_sec": round(cursor + duration, 3),
                "duration_sec": round(duration, 3),
                "source_seek_sec": round(segment["source_seek_sec"], 3),
                "acceptance": segment["acceptance"],
                "audio_segment": str(segment["audio_segment"].relative_to(project)),
                "audio_segment_sha256": segment["audio_segment_sha256"],
                "narration_wavs": [
                    {
                        "path": str(voice.relative_to(project)),
                        "resolved_voice_id": resolved_voice_id,
                        "output_sha256": sha256_file(voice),
                    }
                    for voice in segment["narration_wavs"]
                ],
            }
        )
        cursor += duration

    video_list = video_dir / "concat.txt"
    audio_list = audio_dir / "concat.txt"
    ensure_safe_output(project, video_list)
    ensure_safe_output(project, audio_list)
    video_list.write_text("".join(concat_list_line(path) for path in video_parts), encoding="utf-8")
    audio_list.write_text("".join(concat_list_line(path) for path in audio_parts), encoding="utf-8")

    outputs = config["outputs"]
    for output in outputs.values():
        ensure_safe_output(project, output)
    run(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
            "-i", str(video_list), "-c", "copy", str(outputs["footage_track"]),
        ],
        "concat footage spine",
        video_dir,
    )
    run(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
            "-i", str(audio_list), "-ac", "2", "-ar", "48000",
            "-c:a", "pcm_s16le", str(outputs["master_audio"]),
        ],
        "concat master audio",
        audio_dir,
    )
    timeline = {
        "schema_version": 1,
        "duration_sec": round(cursor, 3),
        "voice_selection": {
            "path": str(config["selection"].relative_to(project)),
            "resolved_voice_id": resolved_voice_id,
        },
        "footage_track": str(outputs["footage_track"].relative_to(project)),
        "master_audio": str(outputs["master_audio"].relative_to(project)),
        "segments": timeline_segments,
    }
    outputs["timeline"].write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[done] timeline duration={cursor:.3f}s segments={len(timeline_segments)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="project directory")
    parser.add_argument(
        "--config", default="build/timeline-config.json", help="project-relative config path"
    )
    parser.add_argument("--check", action="store_true", help="validate config and inputs only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        fail(f"project directory not found: {project}")
    require_tools()
    config_path = resolve_inside(project, args.config, "config")
    config = parse_config(project, load_json(config_path))
    validate_inputs(config, project)
    if args.check:
        total = sum(segment["duration_sec"] for segment in config["segments"])
        print(f"LONGFORM TIMELINE TEMPLATE: PASS segments={len(config['segments'])} duration={total:.3f}s")
        return
    build(config, project)


if __name__ == "__main__":
    main()
