#!/usr/bin/env python3
"""Cut clean vertical showcase footage and extract per-song audio windows."""
import json
import subprocess
from pathlib import Path

import song_config as cfg

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "clips"
ASRC = ROOT / "audio_src"
TMP = ROOT / "build" / "ftmp"
for d in (CLIPS, ASRC, TMP):
    d.mkdir(parents=True, exist_ok=True)

meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


LB = (
    "[0:v]crop={crop},split=2[bg][fg];"
    "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "gblur=sigma=30,eq=brightness=-0.32:saturation=1.08:contrast=1.03[bgb];"
    "[fg]scale=1080:-2[fgs];"
    "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
)


def letterbox_cut(src, ss, dur, crop, out):
    run([
        "ffmpeg", "-v", "error", "-ss", f"{ss}", "-i", src, "-t", f"{dur}",
        "-filter_complex", LB.format(crop=crop),
        "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
        out, "-y",
    ])


for s in cfg.SONGS:
    key = s["key"]
    vdur = meta[key]["dur"]
    seg = cfg.seg_dur(vdur, s["show"])
    foot_dur = round(cfg.PREROLL + s["show"] + 0.6, 3)
    src_video = str(ROOT / s["video"])

    v_start = cfg.footage_window_start(s["chorus"])
    out_show = str(CLIPS / f"show_{key}.mp4")
    letterbox_cut(src_video, v_start, foot_dur, s["crop"], out_show)

    a_start = cfg.audio_window_start(s["chorus"], vdur)
    out_aud = str(ASRC / f"{key}.wav")
    run([
        "ffmpeg", "-v", "error", "-ss", f"{a_start}", "-i", str(ROOT / s["audio_src"]),
        "-t", f"{seg + 0.5}", "-vn", "-ac", "2", "-ar", "48000", out_aud, "-y",
    ])

    vd = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", out_show,
    ]).decode().strip()
    ad = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", out_aud,
    ]).decode().strip()
    print(
        f"{key:18s} show={s['show']:.0f}s  footage={float(vd):.1f}s "
        f"(need {foot_dur:.1f})  audio={float(ad):.1f}s (seg {seg:.1f})  "
        f"v_start={v_start}  a_start={a_start}"
    )

print("PREP DONE")
