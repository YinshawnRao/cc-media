#!/usr/bin/env python3
"""Prepare vertical clips for 王若琳最被低估的5首歌.

- 复仇/聊八卦/漠不关心/大家的孤独：单条耦合窗口（footage+audio 同源同窗）→ vfill 整条源，
  build 再用 foot_seek=mseek 取窗。
- 鬼才出道（#5）：官方MV是电影 tie-in（穿插《鬼才之道》演员 + 惠LIVE 徽标 + 烧词 + glitch 2.35:1 镜头）
  → 解耦：录音室音轨 + **王若琳本人 only 表演镜头蒙太奇**（避演员/徽标/glitch烧词），foot_seek=0。
- vfill.sh 保 -map 0:a，蒙太奇 sub-clip 切片别加 -an（否则 vfill 静默失败，见 memory suhuilun）。
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
C = ROOT / "clips"
C.mkdir(exist_ok=True)
TMP = ROOT / "clips" / "_tmp"
TMP.mkdir(exist_ok=True)
VFILL = str(ROOT.parents[1] / "tools" / "video" / "vfill.sh")


def run(cmd):
    subprocess.run(cmd, check=True)


def cut(src, start, dur, out, extra_v=None):
    """output-seek cut (accurate on webm/av1), keep audio, H.264 dense keyframes."""
    vf = extra_v or "null"
    run(["ffmpeg", "-v", "error", "-i", str(src), "-ss", f"{start}", "-t", f"{dur}",
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30",
         "-keyint_min", "30", "-c:a", "aac", "-b:a", "192k", str(out), "-y"])


def vfill(src, out, crop, br="-0.32", sat="1.06"):
    run(["bash", VFILL, str(src), str(out), crop, br, sat])


def montage(name, src, clips, crop, br="-0.10", sat="1.05"):
    """clips = [(start, dur), ...] her-only sub-clips → cut → vfill → concat."""
    parts = []
    for i, (s, d) in enumerate(clips):
        raw_part = TMP / f"{name}_{i}.mp4"
        cut(src, s, d, raw_part)
        v_part = TMP / f"{name}_{i}_v.mp4"
        vfill(raw_part, v_part, crop, br, sat)
        parts.append(v_part)
    lst = TMP / f"{name}_list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    out = C / f"vert_{name}.mp4"
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30",
         "-keyint_min", "30", "-c:a", "aac", "-b:a", "192k", str(out), "-y"])
    print("montage ->", out, _dur(out))


def _dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return f"{float(r.stdout.strip()):.1f}s"


# ---------- #5 鬼才出道 montage (her-only full-frame performance shots) ----------
P5 = RAW / "p5_guicai_mv.webm"
P5_CROP = "1920:780:0:140"  # letterbox, drop bottom burned-lyrics + top emblem band
montage("p5_guicai", P5,
        [(26.0, 8.0), (94.0, 5.5), (104.0, 8.0), (2.5, 7.5), (228.0, 13.0)], P5_CROP)

# intro footage (mostly hidden behind cover layer) — short #5 her montage
montage("intro", P5, [(2.5, 8.0), (104.0, 7.0), (228.0, 7.0)], P5_CROP)

# ---------- coupled songs: vfill full source (build seeks foot_seek=mseek) ----------
vfill(RAW / "p4b_wall.mkv", C / "vert_p4_liaobagua.mp4", "560:660:400:25", br="-0.18", sat="1.06")
vfill(RAW / "p3_moguanxin_yh.mp4", C / "vert_p3_moguanxin.mp4", "720:890:780:60")
vfill(RAW / "p2_fuchou_kara.mkv", C / "vert_p2_fuchou.mp4", "648:284:0:58")
vfill(RAW / "p1_dajia_zqcp.mp4", C / "vert_p1_dajia.mp4", "1920:1010:0:40")

# outro footage = #1 大家的孤独 站前诚品 lamp-lit wig (atmospheric callback), single window
cut(RAW / "p1_dajia_zqcp.mp4", 120.0, 26.0, TMP / "outro_raw.mp4")
vfill(TMP / "outro_raw.mp4", C / "vert_outro.mp4", "1920:1010:0:40")

# ---------- cover_hero: #5 ghost-glam close-up (striking, recognizable, on-theme) ----------
cov_frame = TMP / "cover_frame.png"
run(["ffmpeg", "-v", "error", "-i", str(P5), "-ss", "3.5", "-frames:v", "1", str(cov_frame), "-y"])
# vertical cover crop centered on her face, scale to 1080x1920 (blurred fill bg)
run(["ffmpeg", "-v", "error", "-i", str(cov_frame), "-filter_complex",
     "[0:v]crop=620:1040:650:30,split=2[bg][fg];"
     "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.20:saturation=1.05[bgb];"
     "[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]",
     "-map", "[v]", "-frames:v", "1", str(ROOT / "cover_hero.png"), "-y"])
print("cover ->", ROOT / "cover_hero.png")

for p in TMP.glob("*"):
    p.unlink()
TMP.rmdir()
print("done prep_clips")
