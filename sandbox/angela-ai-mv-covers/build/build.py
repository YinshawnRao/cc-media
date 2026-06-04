#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATERMARK_TEXT = "AI训练，仅供娱乐"


@dataclass(frozen=True)
class Song:
    key: str
    title: str
    video: str
    song_audio: str
    intro_voice: str
    output: str
    crop: tuple[int, int, int, int] | None = None


SONGS = [
    Song(
        key="guangnianzhiwai",
        title="光年之外",
        video="raw/guangnianzhiwai.mp4",
        song_audio="audio/guangnianzhiwai_e200_final.wav",
        intro_voice="voice/guangnianzhiwai_intro.wav",
        output="final/光年之外_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="tiankongmeiyoujixian",
        title="天空没有极限",
        video="raw/tiankongmeiyoujixian.mp4",
        song_audio="audio/tiankongmeiyoujixian_e200_final.wav",
        intro_voice="voice/tiankongmeiyoujixian_intro.wav",
        output="final/天空没有极限_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="yuai",
        title="雨爱",
        video="raw/yuai.mp4",
        song_audio="audio/yuai_e200_final.wav",
        intro_voice="voice/yuai_intro.wav",
        output="final/雨爱_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="lixiangqingren",
        title="理想情人",
        video="raw/lixiangqingren.mp4",
        song_audio="audio/lixiangqingren_e200_final.wav",
        intro_voice="voice/lixiangqingren_intro.wav",
        output="final/理想情人_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="xinqiang",
        title="心墙",
        video="raw/xinqiang.mp4",
        song_audio="audio/xinqiang_e200_jijin.wav",
        intro_voice="voice/xinqiang_intro.wav",
        output="final/心墙_AI训练张韶涵音色MV.mp4",
        crop=(3840, 1920, 0, 0),
    ),
    Song(
        key="turanxiangqini",
        title="突然想起你",
        video="raw/turanxiangqini.mp4",
        song_audio="audio/turanxiangqini_e200_jijin.wav",
        intro_voice="voice/turanxiangqini_intro.wav",
        output="final/突然想起你_AI训练张韶涵音色MV.mp4",
    ),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def probe_json(path: Path, entries: str, streams: bool = False) -> dict:
    cmd = ["ffprobe", "-v", "error"]
    if streams:
        cmd += ["-select_streams", "v:0"]
    cmd += ["-show_entries", entries, "-of", "json", str(path)]
    out = subprocess.check_output(cmd, cwd=ROOT, text=True)
    return json.loads(out)


def duration(path: Path) -> float:
    info = probe_json(path, "format=duration")
    return float(info["format"]["duration"])


def video_size(path: Path) -> tuple[int, int]:
    info = probe_json(path, "stream=width,height", streams=True)
    stream = info["streams"][0]
    return int(stream["width"]), int(stream["height"])


def even(value: float) -> int:
    rounded = int(round(value))
    return rounded if rounded % 2 == 0 else rounded - 1


def output_size(width: int, height: int) -> tuple[int, int]:
    if width <= 1920:
        return width, height
    return 1920, even(height * 1920 / width)


def compile_watermark_renderer() -> Path:
    source = ROOT / "build" / "watermark.swift"
    binary = ROOT / "build" / "watermark_renderer"
    if binary.exists() and binary.stat().st_mtime >= source.stat().st_mtime:
        return binary

    cache = ROOT / "build" / ".clang-module-cache"
    cache.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CLANG_MODULE_CACHE_PATH"] = str(cache)
    cmd = [
        "swiftc",
        "-target",
        "arm64-apple-macosx15.0",
        str(source),
        "-o",
        str(binary),
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)
    return binary


def make_watermark(renderer: Path, song: Song, out_w: int) -> Path:
    font_size = max(18, round(out_w / 60))
    output = ROOT / "build" / f"{song.key}_watermark.png"
    run([str(renderer), str(output), WATERMARK_TEXT, str(font_size)])
    return output


def speech_window(path: Path) -> tuple[float, float]:
    info = duration(path)
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "silencedetect=n=-35dB:d=0.15",
            "-f",
            "null",
            "-",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    segments: list[tuple[float, float]] = []
    active_start: float | None = None
    for line in proc.stderr.splitlines():
        start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if start_match:
            active_start = float(start_match.group(1))
            continue
        end_match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if end_match:
            segments.append((active_start or 0.0, float(end_match.group(1))))
            active_start = None

    start = 0.0
    end = info
    if segments and segments[0][0] <= 0.05:
        start = min(segments[0][1], info)
    if segments and abs(segments[-1][1] - info) <= 0.08:
        end = max(start + 0.10, segments[-1][0])
    return start, end


def trim_intro_voice(song: Song) -> Path:
    source = ROOT / song.intro_voice
    output = ROOT / "build" / f"{song.key}_intro_trimmed.wav"
    start, end = speech_window(source)
    trimmed_duration = end - start
    fade_out_start = max(0.0, trimmed_duration - 0.04)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            song.intro_voice,
            "-af",
            (
                f"atrim=start={start:.3f}:end={end:.3f},"
                "asetpts=N/SR/TB,"
                "afade=t=in:st=0:d=0.03,"
                f"afade=t=out:st={fade_out_start:.3f}:d=0.04"
            ),
            str(output.relative_to(ROOT)),
        ]
    )
    return output


def filtered_video_size(song: Song) -> tuple[int, int]:
    video_path = ROOT / song.video
    width, height = video_size(video_path)
    if song.crop:
        width, height = song.crop[0], song.crop[1]
    return output_size(width, height)


def ffmpeg_filter(song: Song, voice_path: Path) -> str:
    out_w, out_h = filtered_video_size(song)
    crop_filter = ""
    if song.crop:
        cw, ch, cx, cy = song.crop
        crop_filter = f"crop={cw}:{ch}:{cx}:{cy},"
    inset = max(18, round(out_w / 60))
    voice_delay = 0.15
    duck_end = voice_delay + duration(voice_path) + 0.15
    recover = 0.35
    duck_expr = (
        f"if(lt(t,{duck_end:.3f}),0.25,"
        f"if(lt(t,{duck_end + recover:.3f}),"
        f"0.25+(t-{duck_end:.3f})/{recover:.3f}*0.75,1))"
    )
    video = (
        f"[0:v]{crop_filter}scale={out_w}:{out_h}:flags=lanczos,"
        f"format=rgba[base];"
        f"[3:v]format=rgba[wm];"
        f"[base][wm]overlay=x={inset}:y={inset}:eof_action=repeat,"
        f"format=yuv420p[vout]"
    )
    audio = (
        f"[1:a]volume='{duck_expr}':eval=frame[song];"
        f"[2:a]adelay={int(voice_delay * 1000)}:all=1,volume=1.15[voice];"
        f"[song][voice]amix=inputs=2:duration=first:dropout_transition=0:"
        f"normalize=0,alimiter=limit=0.95[aout]"
    )
    return f"{video};{audio}"


def main() -> None:
    renderer = compile_watermark_renderer()
    (ROOT / "final").mkdir(exist_ok=True)
    requested = set(sys.argv[1:])
    if requested:
        known = {song.key for song in SONGS}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"Unknown song key(s): {', '.join(unknown)}")
    songs = [song for song in SONGS if not requested or song.key in requested]
    for song in songs:
        output = ROOT / song.output
        output.parent.mkdir(parents=True, exist_ok=True)
        out_w, _ = filtered_video_size(song)
        voice = trim_intro_voice(song)
        watermark = make_watermark(renderer, song, out_w)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                song.video,
                "-i",
                song.song_audio,
                "-i",
                str(voice.relative_to(ROOT)),
                "-loop",
                "1",
                "-i",
                str(watermark.relative_to(ROOT)),
                "-filter_complex",
                ffmpeg_filter(song, voice),
                "-map",
                "[vout]",
                "-map",
                "[aout]",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                "-shortest",
                song.output,
            ]
        )


if __name__ == "__main__":
    main()
