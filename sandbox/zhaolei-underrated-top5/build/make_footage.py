#!/usr/bin/env python3
"""Build vert_<key>.mp4 footage clips from montage recipes (multi-source, decoupled).

Each recipe = list of (src, start, dur, crop) cut from raw sources, normalized to a
common canvas (CANVAS_W x CANVAS_H, scale+pad centered), concatenated, then run through
vfill-equivalent (blur-fill letterbox to 1080x1920, no extra crop since already cropped).
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
RES = ROOT / "probe" / "research" / "dl"
CLIPS = ROOT / "clips"
TMP = ROOT / "probe" / "_montage_tmp"
TMP.mkdir(parents=True, exist_ok=True)
CLIPS.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1600, 900


def run(cmd):
    subprocess.run(cmd, check=True)


def cut_piece(src, start, dur, crop, out):
    vf = f"crop={crop},scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=decrease,pad={CANVAS_W}:{CANVAS_H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30"
    run([
        "ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", str(src),
        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-g", "30", "-keyint_min", "30",
        str(out),
    ])


def build_montage(key, pieces):
    piece_files = []
    for i, (src, start, dur, crop) in enumerate(pieces):
        out = TMP / f"{key}_{i}.mp4"
        cut_piece(src, start, dur, crop, out)
        piece_files.append(out)
    listfile = TMP / f"{key}_list.txt"
    listfile.write_text("".join(f"file '{p.resolve()}'\n" for p in piece_files), encoding="utf-8")
    concat_out = TMP / f"{key}_concat.mp4"
    run([
        "ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-g", "30", "-keyint_min", "30",
        str(concat_out),
    ])
    return concat_out


def vfill(src, out, brightness=-0.32, saturation=1.06):
    """Full-width letterbox to 1080x1920 (src already clean-cropped, no further crop)."""
    filt = (
        f"[0:v]split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness={brightness}:saturation={saturation}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run([
        "ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", filt,
        "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(out),
    ])


RECIPES = {
    "p5_buka": [
        (RES / "chengdu_mv_full.mp4", 30, 18, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 58, 18, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 84, 10, "1920:850:0:0"),
    ],
    "p4_hadesen": [
        (RES / "hadesen_full60.mp4", 30, 20, "1280:510:0:100"),
        (RES / "hadesen_tail.mp4", 12, 10, "1280:510:0:100"),  # tail.mp4 starts at 160s -> local 172-160=12
        (RES / "chengdu_mv_full.mp4", 136, 12, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 188, 6, "1920:850:0:0"),
    ],
    "p3_mali": [
        (RES / "chengdu_mv_full.mp4", 96, 5, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 104, 7, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 188, 10, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 198, 12, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 210, 10, "1920:850:0:0"),
    ],
    "p2_renjia": [
        (RAW / "p2_renjia_full.mp4", 30, 55, "640:300:0:60"),
    ],
    "p1_xin": [
        (RES / "p4_weigei_mv_BV13W411L7WN.mp4", 0, 20, "1920:740:0:140"),
        (RES / "chengdu_mv_full.mp4", 58, 18, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 40, 18, "1920:850:0:0"),
        (RES / "chengdu_mv_full.mp4", 192, 6, "1920:850:0:0"),
    ],
    "intro": [
        (RAW / "p2_renjia_full.mp4", 140, 20, "640:300:0:60"),
    ],
    "outro": [
        (RAW / "p2_renjia_full.mp4", 180, 35, "640:300:0:60"),
    ],
}

if __name__ == "__main__":
    import sys
    keys = sys.argv[1:] or list(RECIPES.keys())
    for key in keys:
        pieces = RECIPES[key]
        concat_out = build_montage(key, pieces)
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(concat_out)],
                              capture_output=True, text=True).stdout.strip()
        out = CLIPS / f"vert_{key}.mp4"
        vfill(concat_out, out)
        print(f"{key}: montage {dur}s -> {out}")
