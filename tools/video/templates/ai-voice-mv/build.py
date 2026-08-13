#!/usr/bin/env python3
"""Build one-MP4-per-song AI voice MVs from project-local inputs.

This is a media-only template. It never downloads sources, reads cookies, scans
external voice projects, or generates TTS. See the sibling README section in
``tools/video/templates/README.md`` before use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, NoReturn


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.video import resource_budget  # noqa: E402


KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class Song:
    key: str
    title: str
    video: Path
    song_audio: Path
    intro_voice: Path
    output_name: str
    crop: tuple[int, int, int, int] | None
    audio_gain: float


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
    # Keep the logical path so output validation can still see and reject an
    # in-project symlink instead of silently following it to another target.
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


def parse_crop(value: Any, label: str) -> tuple[int, int, int, int] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 4:
        fail(f"{label} must be null or [width, height, x, y]")
    if any(not isinstance(item, int) or isinstance(item, bool) for item in value):
        fail(f"{label} values must be integers")
    width, height, x, y = value
    if width <= 0 or height <= 0 or x < 0 or y < 0:
        fail(f"{label} has invalid dimensions")
    if width % 2 or height % 2:
        fail(f"{label} width and height must be even for H.264")
    return width, height, x, y


def parse_config(project: Path, config: dict[str, Any]) -> tuple[list[Song], dict[str, Any]]:
    if config.get("schema_version") != 1:
        fail("unsupported config schema_version; expected 1")

    selection = resolve_inside(project, config.get("voice_selection"), "voice_selection")
    output_dir_raw = config.get("output_dir", "renders")
    if output_dir_raw != "renders":
        fail("output_dir must be exactly 'renders'")
    output_dir = resolve_inside(project, output_dir_raw, "output_dir")
    watermark_png = resolve_inside(project, config.get("watermark_png"), "watermark_png")

    rows = config.get("songs")
    if not isinstance(rows, list) or not rows:
        fail("songs must be a non-empty array")

    songs: list[Song] = []
    seen: set[str] = set()
    seen_outputs: set[Path] = set()
    for index, row in enumerate(rows):
        label = f"songs[{index}]"
        if not isinstance(row, dict):
            fail(f"{label} must be an object")
        key = row.get("key")
        if not isinstance(key, str) or not KEY_RE.fullmatch(key):
            fail(f"{label}.key must match {KEY_RE.pattern}")
        if key in seen:
            fail(f"duplicate song key: {key}")
        seen.add(key)

        title = row.get("title")
        output_name = row.get("output")
        if not isinstance(title, str) or not title.strip():
            fail(f"{label}.title must be non-empty")
        if not isinstance(output_name, str) or not output_name.strip():
            fail(f"{label}.output must be non-empty")
        output_path = Path(output_name)
        if output_path.is_absolute() or ".." in output_path.parts:
            fail(f"{label}.output must be a relative output name")
        if output_path.suffix.lower() != ".mp4":
            fail(f"{label}.output must end in .mp4")
        if output_path in seen_outputs:
            fail(f"duplicate song output: {output_name}")
        seen_outputs.add(output_path)

        gain = row.get("audio_gain", 1.0)
        if not isinstance(gain, (int, float)) or isinstance(gain, bool) or not 0 < float(gain) <= 4:
            fail(f"{label}.audio_gain must be in (0, 4]")
        songs.append(
            Song(
                key=key,
                title=title.strip(),
                video=resolve_inside(project, row.get("video"), f"{label}.video"),
                song_audio=resolve_inside(project, row.get("song_audio"), f"{label}.song_audio"),
                intro_voice=resolve_inside(project, row.get("intro_voice"), f"{label}.intro_voice"),
                output_name=output_name,
                crop=parse_crop(row.get("crop"), f"{label}.crop"),
                audio_gain=float(gain),
            )
        )

    settings = {
        "selection": selection,
        "output_dir": output_dir,
        "watermark_png": watermark_png,
    }
    return songs, settings


def validate_inputs(songs: list[Song], settings: dict[str, Any], project: Path) -> None:
    missing: list[Path] = []
    sidecars: dict[str, Path] = {}
    for path in [settings["selection"]]:
        if not path.is_file():
            missing.append(path)
    if not settings["watermark_png"].is_file():
        missing.append(settings["watermark_png"])
    for song in songs:
        for path in (song.video, song.song_audio, song.intro_voice):
            if not path.is_file():
                missing.append(path)
        sidecar = sidecar_path(project, song.intro_voice)
        sidecars[song.key] = sidecar
        if not sidecar.is_file():
            missing.append(sidecar)
    if missing:
        rendered = "\n".join(f"  - {path}" for path in missing)
        fail(f"missing required project inputs:\n{rendered}")

    selection = load_json(settings["selection"])
    expected_voice = selection.get("resolved_voice_id")
    if not isinstance(expected_voice, str) or not expected_voice.strip():
        fail("voice-selection.json resolved_voice_id must be non-empty")
    for song in songs:
        sidecar = load_json(sidecars[song.key])
        if sidecar.get("selection") != selection:
            fail(f"intro sidecar selection does not match voice-selection.json: {song.key}")
        if sidecar.get("resolved_voice_id") != expected_voice:
            fail(f"intro sidecar resolved voice does not match project selection: {song.key}")
        if sidecar.get("output_sha256") != sha256_file(song.intro_voice):
            fail(f"intro sidecar output hash does not match intro WAV: {song.key}")

        video_duration = duration(song.video)
        song_duration = duration(song.song_audio)
        intro_start, intro_end = speech_window(song.intro_voice)
        intro_duration = intro_end - intro_start
        if video_duration + 0.50 < song_duration:
            fail(
                f"{song.key} video is {video_duration:.3f}s but song audio is "
                f"{song_duration:.3f}s; align/precut the MV before build"
            )
        if intro_duration + 1.0 >= song_duration:
            fail(
                f"{song.key} intro is too long for {song_duration:.3f}s song audio"
            )


def require_tools() -> None:
    names = ["ffmpeg", "ffprobe"]
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        fail(f"missing required command(s): {', '.join(missing)}")


def _budgeted_ffmpeg_command(command: list[str], threads: int) -> list[str]:
    """Apply one lease's decoder/filter/encoder budget to an FFmpeg command."""

    if len(command) < 2 or Path(command[0]).name != "ffmpeg":
        raise ValueError("run() only accepts an FFmpeg command")
    value = str(threads)
    return [
        command[0],
        "-threads",
        value,
        "-filter_threads",
        value,
        "-filter_complex_threads",
        value,
        *command[1:-1],
        "-threads",
        value,
        command[-1],
    ]


def run(
    command: list[str],
    label: str,
    cwd: Path,
    **subprocess_options: Any,
) -> subprocess.CompletedProcess[Any]:
    print(f"[run] {label}")
    with resource_budget.resolve_ffmpeg_threads() as lease:
        return subprocess.run(
            _budgeted_ffmpeg_command(command, lease.threads),
            cwd=cwd,
            check=True,
            **subprocess_options,
        )


def probe_json(path: Path, entries: str, select_video: bool = False) -> dict[str, Any]:
    command = ["ffprobe", "-v", "error"]
    if select_video:
        command += ["-select_streams", "v:0"]
    command += ["-show_entries", entries, "-of", "json", str(path)]
    return json.loads(subprocess.check_output(command, text=True))


def duration(path: Path) -> float:
    value = probe_json(path, "format=duration")
    return float(value["format"]["duration"])


def source_video_size(path: Path) -> tuple[int, int]:
    value = probe_json(path, "stream=width,height", select_video=True)
    stream = value["streams"][0]
    return int(stream["width"]), int(stream["height"])


def even(value: float) -> int:
    rounded = int(round(value))
    return rounded if rounded % 2 == 0 else rounded - 1


def filtered_video_size(song: Song) -> tuple[int, int]:
    source_width, source_height = source_video_size(song.video)
    width, height = source_width, source_height
    if song.crop:
        width, height, x, y = song.crop
        if x + width > source_width or y + height > source_height:
            fail(f"crop for {song.key} exceeds source bounds {source_width}x{source_height}")
    if width > 1920:
        return 1920, even(height * 1920 / width)
    return width, height


def speech_window(path: Path) -> tuple[float, float]:
    total = duration(path)
    process = run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
            "-af", "silencedetect=n=-35dB:d=0.15", "-f", "null", "-",
        ],
        "detect intro speech window",
        path.parent,
        text=True,
        capture_output=True,
    )
    silences: list[tuple[float, float]] = []
    pending_start: float | None = None
    for line in process.stderr.splitlines():
        start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if start_match:
            pending_start = float(start_match.group(1))
            continue
        end_match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if end_match:
            silences.append((pending_start or 0.0, float(end_match.group(1))))
            pending_start = None

    start, end = 0.0, total
    if silences and silences[0][0] <= 0.05:
        start = min(silences[0][1], total)
    if silences and abs(silences[-1][1] - total) <= 0.08:
        end = max(start + 0.10, silences[-1][0])
    return start, end


def trim_voice(song: Song, cache_dir: Path, project: Path) -> Path:
    output = cache_dir / f"{song.key}-intro-trimmed.wav"
    ensure_safe_output(project, output)
    start, end = speech_window(song.intro_voice)
    trimmed = end - start
    fade_out = max(0.0, trimmed - 0.04)
    run(
        [
            "ffmpeg", "-y", "-i", str(song.intro_voice), "-af",
            (
                f"atrim=start={start:.3f}:end={end:.3f},asetpts=N/SR/TB,"
                f"afade=t=in:st=0:d=0.03,afade=t=out:st={fade_out:.3f}:d=0.04"
            ),
            str(output),
        ],
        f"trim intro {song.key}",
        project,
    )
    return output


def filter_graph(song: Song, voice: Path, output_width: int) -> str:
    output_height = filtered_video_size(song)[1]
    crop = ""
    if song.crop:
        width, height, x, y = song.crop
        crop = f"crop={width}:{height}:{x}:{y},"
    inset = max(18, round(output_width / 60))
    delay = 0.15
    duck_end = delay + duration(voice) + 0.15
    recovery = 0.35
    duck = (
        f"if(lt(t,{duck_end:.3f}),0.25,"
        f"if(lt(t,{duck_end + recovery:.3f}),"
        f"0.25+(t-{duck_end:.3f})/{recovery:.3f}*0.75,1))"
    )
    video = (
        f"[0:v]{crop}tpad=stop_mode=clone:stop_duration=2,"
        f"scale={output_width}:{output_height}:flags=lanczos,format=rgba[base];"
        f"[3:v]format=rgba[wm];"
        f"[base][wm]overlay=x={inset}:y={inset}:eof_action=repeat,format=yuv420p[vout]"
    )
    audio = (
        f"[1:a]volume='{song.audio_gain:.4f}*({duck})':eval=frame[song];"
        f"[2:a]adelay={int(delay * 1000)}:all=1,volume=1.15[voice];"
        "[song][voice]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.95[aout]"
    )
    return f"{video};{audio}"


def build_song(
    song: Song,
    project: Path,
    output: Path,
    watermark: Path,
    cache_dir: Path,
) -> None:
    voice = trim_voice(song, cache_dir, project)
    width, _ = filtered_video_size(song)
    ensure_safe_output(project, output)
    run(
        [
            "ffmpeg", "-y",
            "-i", str(song.video),
            "-i", str(song.song_audio),
            "-i", str(voice),
            "-loop", "1", "-i", str(watermark),
            "-filter_complex", filter_graph(song, voice, width),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-shortest", str(output),
        ],
        f"build {song.key}",
        project,
    )


def ensure_safe_output(project: Path, output: Path) -> None:
    """Reject output symlinks and parents that could escape the project."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys", nargs="*", help="optional song keys; default builds all")
    parser.add_argument("--project", required=True, help="project directory")
    parser.add_argument("--config", default="build/config.json", help="project-relative config path")
    parser.add_argument("--date", help="output batch date, YYYY-MM-DD; default today")
    parser.add_argument("--check", action="store_true", help="validate config and local inputs only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        fail(f"project directory not found: {project}")
    config_path = resolve_inside(project, args.config, "config")
    songs, settings = parse_config(project, load_json(config_path))

    requested = set(args.keys)
    known = {song.key for song in songs}
    unknown = sorted(requested - known)
    if unknown:
        fail(f"unknown song key(s): {', '.join(unknown)}")
    songs = [song for song in songs if not requested or song.key in requested]
    require_tools()
    validate_inputs(songs, settings, project)

    if args.check:
        print(f"AI VOICE MV TEMPLATE: PASS songs={len(songs)}")
        return

    batch_date = args.date or date.today().isoformat()
    try:
        date.fromisoformat(batch_date)
    except ValueError:
        fail("--date must use YYYY-MM-DD")
    output_dir_relative = settings["output_dir"].relative_to(project)
    cache_dir = resolve_inside(project, "tmp/ai-voice-mv", "cache directory")
    ensure_safe_directory(project, cache_dir)

    for song in songs:
        output_relative = output_dir_relative / batch_date / song.output_name
        output = resolve_inside(project, str(output_relative), f"output for {song.key}")
        ensure_safe_output(project, output)
        build_song(song, project, output, settings["watermark_png"], cache_dir)
        print(f"[done] {output.relative_to(project)}")


if __name__ == "__main__":
    main()
