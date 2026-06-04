#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
CLIPS = ROOT / "clips"
CLIPS.mkdir(exist_ok=True)

COMMON_BG = "-0.30"
COMMON_SAT = "1.07"

CLIP_SPECS = [
    {
        "key": "top5_chinastar",
        "raw": "top5_chinastar.mp4",
        "start": 226.575,
        "duration": 60.0,
        "crop": "1100:900:410:80",
        "boxes": [(480, 0, 360, 90), (0, 610, 1100, 150)],
    },
    {
        "key": "top4_korea2002",
        "raw": "top4_korea2002.mp4",
        "start": 112.425,
        "duration": 60.0,
        "crop": "950:720:421:80",
        "boxes": [(0, 585, 950, 135)],
    },
    {
        "key": "top3_changchun2003",
        "raw": "top3_changchun2003.mp4",
        "start": 105.525,
        "duration": 60.0,
        "crop": "1600:1400:550:300",
        "boxes": [(0, 1130, 1600, 150)],
    },
    {
        "key": "top2_singer2024",
        "raw": "top2_singer2024.mp4",
        "start": 224.25,
        "duration": 65.0,
        "crop": "1100:900:410:110",
        "boxes": [(0, 610, 680, 170)],
    },
    {
        "key": "top1_korea5",
        "raw": "top1_korea5_originalkey.mp4",
        "start": 219.475,
        "duration": 53.6,
        "crop": "520:500:136:50",
        "boxes": [(0, 382, 520, 118)],
    },
]


def drawboxes(boxes):
    parts = []
    for x, y, w, h in boxes:
        parts.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=black@0.80:t=fill")
    return ",".join(parts)


def run(spec):
    out = CLIPS / f"{spec['key']}.mp4"
    source = RAW / spec["raw"]
    clean = drawboxes(spec["boxes"])
    filter_graph = (
        f"[0:v]crop={spec['crop']},{clean},split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,gblur=sigma=34,eq=brightness={COMMON_BG}:saturation={COMMON_SAT}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        str(spec["start"]),
        "-t",
        str(spec["duration"]),
        "-i",
        str(source),
        "-filter_complex",
        filter_graph,
        "-map",
        "[v]",
        "-map",
        "0:a",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-r",
        "30",
        "-g",
        "30",
        "-keyint_min",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(out),
        "-y",
    ]
    print("processing", spec["key"])
    subprocess.run(cmd, check=True)
    subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(out),
        ],
        check=True,
    )


for spec in CLIP_SPECS:
    run(spec)
