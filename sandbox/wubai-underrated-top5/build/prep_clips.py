#!/usr/bin/env python3
"""Prep vertical clips for Wu Bai underrated top5.

Every song uses a CONTINUOUS Wu-Bai-dominant window, letterboxed (4:3 -> 1080x1920),
bottom karaoke lyric cropped off.

- type "mv"      : official MV, video + its OWN studio audio (same-source, lip-synced).
- type "montage" : the song has NO dedicated footage; use a Wu Bai closeup performance/
  concept MV from the SAME ALBUM as visuals + the target song's STUDIO recording as audio
  (montage救场, decoupled, user-approved). chorus positioned at the showcase offset.

Output: clips/vert_<key>.mp4   Timing constants MUST match full_build.py.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
CLIPS = ROOT / "clips"
TMP = ROOT / "build" / "tmp"
VFILL = ROOT.parents[1] / "tools" / "video" / "vfill.sh"

# --- timing constants (keep in sync with full_build.py) ---
LEAD = 0.35
DIG = 1.5
SHOW = 29.0
POST_NARR = 0.25
MARGIN = 1.6

LETTERBOX = (
    "[0:v]crop={crop},split=2[bg][fg];"
    "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "gblur=sigma=30,eq=brightness=-0.32:saturation=1.06[bgb];"
    "[fg]scale=1080:-2[fgs];"
    "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
)

SONGS = [
    # 来不及: 浪人情歌 MV (same album, intimate concept) + studio audio
    {"key": "p5_laibuji", "type": "montage", "source": "mvsrc_langren",
     "vid_start": 20.0, "crop": "1440:915:0:0", "music": "audio_laibuji", "chorus": 89.0},
    # 飞在风中的小雨: official MV, same-source
    {"key": "p4_feiyu", "type": "mv", "source": "feiyu_mv", "crop": "1440:915:0:0"},
    # 没人爱的女孩: 爱上别人是快乐的事 MV (SAME album 1992, rock performance) + studio audio
    {"key": "p3_meiren", "type": "montage", "source": "mvsrc_aishang",
     "vid_start": 2.0, "crop": "1440:850:0:0", "music": "audio_meiren", "chorus": 228.0},
    # 亲爱的，你喝醉了: official MV, same-source
    {"key": "p2_zuile", "type": "mv", "source": "zuile_mv", "crop": "1440:915:0:0"},
    # 破碎的收音机: 无声的所在 MV (same album 树枝孤鸟, sustained moody closeups) + studio audio
    {"key": "p1_shouyinji", "type": "montage", "source": "mvsrc_wusheng",
     "vid_start": 26.0, "crop": "1440:915:0:0", "music": "audio_shouyinji", "chorus": 24.0},
]


def run(cmd):
    subprocess.run(cmd, check=True)


def vdur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip())


def main():
    CLIPS.mkdir(exist_ok=True)
    TMP.mkdir(exist_ok=True)
    narr = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
    for s in SONGS:
        voice = narr[s["key"]]["dur"]
        pre_off = LEAD + voice + POST_NARR + DIG
        block = pre_off + SHOW
        clip_len = round(block + MARGIN, 3)
        out = CLIPS / f"vert_{s['key']}.mp4"
        src = next(RAW.glob(f"{s['source']}.*"))
        if s["type"] == "mv":
            trimmed = TMP / f"trim_{s['key']}.mp4"
            run(["ffmpeg", "-v", "error", "-i", str(src), "-t", str(clip_len),
                 "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", str(trimmed), "-y"])
            run(["bash", str(VFILL), str(trimmed), str(out), s["crop"]])
        else:
            vstart = s["vid_start"]
            music_start = round(s["chorus"] - pre_off, 3)
            assert music_start >= 0, f"{s['key']} music_start<0"
            run(["ffmpeg", "-v", "error",
                 "-ss", str(vstart), "-i", str(src),
                 "-ss", str(music_start), "-i", str(RAW / f"{s['music']}.wav"),
                 "-filter_complex", LETTERBOX.format(crop=s["crop"]),
                 "-map", "[v]", "-map", "1:a", "-t", str(clip_len),
                 "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
                 "-c:a", "aac", "-b:a", "192k", str(out), "-y"])
        print(f"{s['key']:14s} pre_off={pre_off:5.2f} block={block:5.2f} clip_len={clip_len:5.2f} -> {out.name} dur={vdur(out):.2f} ({s['type']})")


if __name__ == "__main__":
    main()
