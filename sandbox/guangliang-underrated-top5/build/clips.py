#!/usr/bin/env python3
"""切 footage（delogo+crop+letterbox 1080x1920）并产出每首的 music/<key>.wav。

每首：pre = LEAD + voice_dur + 0.25 + DIG，clip_len = pre + show + TAIL_BUF。
- 同源曲(asrc=None)：video 从 vsrc 的 (chorus - pre) 切；music = 该 clip 的音轨（同窗 -> 口型同步）。
- 解耦曲(asrc=wav)：video 从 vsrc 的 vstart 切（独立 B-roll）；music = asrc 的 (chorus - pre)。
两步：① output-seek 重编码 H.264+AAC（修 webm seek + 补音轨）② delogo+crop+letterbox。
vsrc 不存在的歌自动跳过（B-roll 还没下时可先只切已有的）。另切 vert_cover 作封面/片尾底。

用法: python build/clips.py [key1 key2 ...]   不带参数 = 全部（存在源的）
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import song_cfg as cfg

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "clips").mkdir(exist_ok=True)
(ROOT / "music").mkdir(exist_ok=True)
import json
narr = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def letterbox_filter(crop, delogo, bright, sat, grade=""):
    pre = f"delogo=x={delogo.split(':')[0]}:y={delogo.split(':')[1]}:w={delogo.split(':')[2]}:h={delogo.split(':')[3]}," if delogo else ""
    g = f"{grade}," if grade else ""
    return (
        f"[0:v]{g}{pre}crop={crop},split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=30,eq=brightness={bright}:saturation={sat}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )


def make_vert(src, out, start, length, crop, delogo, bright, sat, keep_audio, grade=""):
    cut = ROOT / "raw" / f"cut_{out.stem}.mp4"
    run([
        "ffmpeg", "-v", "error", "-i", str(ROOT / src), "-ss", str(start), "-t", str(length),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(cut), "-y",
    ])
    fc = letterbox_filter(crop, delogo, bright, sat, grade)
    cmd = ["ffmpeg", "-v", "error", "-i", str(cut), "-filter_complex", fc, "-map", "[v]"]
    if keep_audio:
        cmd += ["-map", "0:a"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", "30", "-g", "30", "-keyint_min", "30"]
    if keep_audio:
        cmd += ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
    cmd += [str(out), "-y"]
    run(cmd)


only = set(sys.argv[1:])

# --- cover/outro background clip ---
if (not only or "cover" in only) and (ROOT / cfg.COVER_SRC).exists():
    make_vert(cfg.COVER_SRC, ROOT / "clips" / "vert_cover.mp4", cfg.COVER_START, cfg.COVER_LEN,
              cfg.COVER_CROP, cfg.COVER_DELOGO, -0.30, 1.06, keep_audio=False)
    print("wrote clips/vert_cover.mp4")

for s in cfg.SONGS:
    key = s["key"]
    if only and key not in only:
        continue
    if not (ROOT / s["vsrc"]).exists():
        print(f"[skip] {key}: vsrc missing ({s['vsrc']})")
        continue
    voice = narr[key]["dur"]
    pre = cfg.LEAD + voice + 0.25 + cfg.DIG
    clip_len = round(pre + s["show"] + cfg.TAIL_BUF, 2)
    decoupled = s["asrc"] is not None
    vstart = s["vstart"] if decoupled else round(s["chorus"] - pre, 2)
    out = ROOT / "clips" / f"vert_{key}.mp4"
    print(f"[{key}] decoupled={decoupled} vstart={vstart} len={clip_len} (pre={pre:.2f} show={s['show']}) crop={s['crop']} grade={s.get('grade','')}")
    make_vert(s["vsrc"], out, vstart, clip_len, s["crop"], s["delogo"], s["bright"], s["sat"],
              keep_audio=not decoupled, grade=s.get("grade", ""))
    # music
    music = ROOT / "music" / f"{key}.wav"
    if decoupled:
        astart = round(s["chorus"] - pre, 2)
        run(["ffmpeg", "-v", "error", "-ss", str(astart), "-i", str(ROOT / s["asrc"]), "-t", str(clip_len),
             "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(music), "-y"])
    else:
        run(["ffmpeg", "-v", "error", "-i", str(out), "-vn", "-ac", "2", "-ar", "48000",
             "-c:a", "pcm_s16le", str(music), "-y"])
    print(f"   -> {out}  +  music/{key}.wav")

print("clips done")
