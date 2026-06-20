#!/usr/bin/env python3
"""切 5 首展示 footage 并竖屏化（letterbox）。

每首：clip_src_start = chorus - PRE，PRE = LEAD + voice_dur + 0.25 + DIG。
clip_len = PRE + show + TAIL_BUF。输出端 seek 重编码 H.264+AAC（修 webm/AV1 seek + 补音轨），
再 vfill.sh 全宽 crop -> letterbox 1080x1920。intro/outro 复用对应 vert clip，无需额外切。
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import song_cfg as cfg

ROOT = Path(__file__).resolve().parents[1]
VFILL = ROOT.parents[1] / "tools" / "video" / "vfill.sh"
narr = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


only = set(sys.argv[1:])
for s in cfg.SONGS:
    key = s["key"]
    if only and key not in only:
        continue
    voice = narr[key]["dur"]
    pre = cfg.LEAD + voice + 0.25 + cfg.DIG
    src_start = round(s["chorus"] - pre, 2)
    clip_len = round(pre + s["show"] + cfg.TAIL_BUF, 2)
    cut = ROOT / "raw" / f"cut_{key}.mp4"
    print(f"[{key}] src_start={src_start} len={clip_len} (pre={pre:.2f} show={s['show']}) crop={s['crop']}")
    # 输出端 seek 重编码，保留窗内音轨（与画面同窗 -> 口型同步）
    run([
        "ffmpeg", "-v", "error", "-i", str(ROOT / s["source"]),
        "-ss", str(src_start), "-t", str(clip_len),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        str(cut), "-y",
    ])
    out = ROOT / "clips" / f"vert_{key.split('_',1)[1]}.mp4"
    run(["bash", str(VFILL), str(cut), str(out), s["crop"]])
    print(f"   -> {out}")

print("clips done")
