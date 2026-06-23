#!/usr/bin/env python3
"""Trim source windows and build vertical 1080x1920 clips."""
import contextlib
import json
import subprocess
import wave

from project import (
    AUDIO,
    CLIPS,
    DIG,
    INTRO_GAP,
    INTRO_VOICE_START,
    ITEMS,
    LEAD,
    ROOT,
    VOCAL_UNDER_NARRATION,
)


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


def render_clip(src, out, start, length, crop, br, sat):
    filt = (
        f"[0:v]crop={crop},setsar=1,split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,gblur=sigma=30,eq=brightness={br}:saturation={sat}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(q(start)),
        "-i", src,
        "-t", str(q(length)),
        "-filter_complex", filt,
        "-map", "[v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-r", "30",
        "-g", "30",
        "-keyint_min", "30",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ac", "2",
        "-ar", "48000",
        out,
        "-y",
    ])


def main():
    CLIPS.mkdir(parents=True, exist_ok=True)
    d_intro = dur(AUDIO / "intro.wav")
    plan = {
        "intro": {
            "source": "raw/aimei_bili_seedvr.mp4",
            "start": 170.0,
            "length": q(INTRO_VOICE_START + d_intro + INTRO_GAP + 0.8),
            "crop": "1620:980:0:80",
        },
        "items": [],
    }
    render_clip(
        str(ROOT / plan["intro"]["source"]),
        str(CLIPS / "vert_cover.mp4"),
        plan["intro"]["start"],
        plan["intro"]["length"],
        plan["intro"]["crop"],
        "-0.24",
        "1.05",
    )
    print("cover", plan["intro"])

    for item in ITEMS:
        voice_dur = dur(AUDIO / f"{item['key']}.wav")
        full_start_local = q(LEAD + voice_dur + 0.25 + DIG)
        vocal_local = q(LEAD + voice_dur - VOCAL_UNDER_NARRATION)
        clip_start = max(0.0, q(item["vocal_onset"] - vocal_local))
        seg_len = q(full_start_local + item["show"] + 0.8)
        out = CLIPS / f"vert_{item['key']}.mp4"
        render_clip(
            str(ROOT / item["raw"]),
            str(out),
            clip_start,
            seg_len,
            item["crop"],
            item["br"],
            item["sat"],
        )
        row = {
            "key": item["key"],
            "source": item["raw"],
            "bvid": item["bvid"],
            "clip_start": clip_start,
            "length": seg_len,
            "vocal_onset": item["vocal_onset"],
            "full_start_local": full_start_local,
            "show": item["show"],
            "crop": item["crop"],
        }
        plan["items"].append(row)
        print(item["key"], row)

    (ROOT / "clip_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
