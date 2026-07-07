#!/usr/bin/env python3
"""Build decoupled footage montages (vert_<key>.mp4) for 梁咏琪最被低估的5首歌.

选源现实：这 5 首冷门曲官方上传都是「静态专辑封面 + 录音」(Art Track)，无真 MV。
→ 解耦：音频用官方录音室版（raw/pN_aud.wav），画面用梁咏琪本人**其他真 MV**的特写蒙太奇。
画面源都是 B站修复版（weazegigi / AlfredSE），带角标水印 / 圆角 AI 边框 / 烧词 → 逐源定 crop 裁净。
每首拼 ~52s 连续特写/中景（避开男主/综艺角标/抽象空镜/烧词），letterbox 保原比例。

跨年代分散（避免审美疲劳）：
  #5 地球的住客 ← 他喜欢的是你 MV (2001，同碟)
  #4 喜剧收场   ← 继续爱 MV (2001，同碟 G For Girl，暖金特写)
  #3 旅程       ← 短发 MV (1996，同期短发清新)
  #2 荷花       ← 花火 MV (2000，冷绿调，贴荷花清冷东方感)
  #1 失散车站   ← 出走地平线 MV (2001，同碟，明亮特写，压轴)
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
C = ROOT / "clips"
M = C / "_mont"
M.mkdir(parents=True, exist_ok=True)

# crop = 去水印/圆角/烧词后的全宽横带；bright/sat = FG+BG 提亮（暗源）；windows = [(src_start, dur), ...]
SONGS = {
    "p1_shisan": dict(  # 失散车站 ← 出走地平线 MV (weazegigi 1440x1080，圆角内嵌 + 右上水印 y45-90)；夏日明亮贴"停在某个夏天"
        src="mv_shisan.mp4", crop="1260:880:90:112", bright=0.04, sat=1.06,
        windows=[(22, 18), (58, 14), (90, 14)]),  # 明亮特写+她地平线远景；避 zebra@50,107 / 摄影机@42,56 / 树空镜@74 / 白马@116
    "p2_hehua": dict(  # 花火 (weazegigi 1920x1080，宽银幕信箱 + 左上 weazegigi y21-53 + 右下 WG，暗→提亮)
        src="mv_hehua.mp4", crop="1920:798:0:142", bright=0.13, sat=1.10,
        windows=[(12, 33), (150, 19)]),  # 冷绿调，烟花=花火题意；避末尾手部虚焦
    "p3_lvcheng": dict(  # 旅程 ← 短发 MV (weazegigi 1440x1080，顶部干净，底部烧词 y860)
        src="mv_duanfa.mp4", crop="1440:820:0:0", bright=0.03, sat=1.05,
        windows=[(168, 26), (214, 24)]),  # 亮调暖特写；避前段暗 silhouette 舞 + 烧词 + 末尾人群
    "p4_xiju": dict(  # 喜剧收场 ← 继续爱 MV (weazegigi 1920x1080，右下 WG 角标，暖金特写；中后段暗+男主@175)
        src="mv_jixuai.mp4", crop="1920:850:0:40", bright=0.10, sat=1.07,
        windows=[(42, 52)]),  # 仅用前段暖金特写(她独唱)，避暗段+男主
    "p5_diqiu": dict(  # 地球的住客 ← 新鲜 MV (weazegigi 1920x1080，顶部干净无水印，底部烧词 y900)；绿野自然贴"地球的住客"
        src="mv_xinxian.mp4", crop="1920:880:0:0", bright=0.06, sat=1.06,
        windows=[(115, 30), (188, 22)]),  # 她绿野特写/中景(130/200 特写)；避纯天空空镜@150
}


def letterbox(src, start, dur, crop, bright, sat, out):
    fc = (
        f"[0:v]crop={crop},eq=brightness={bright}:saturation={sat}[c];"
        f"[c]split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=26,eq=brightness=-0.34:saturation=1.0[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    subprocess.run([
        "ffmpeg", "-v", "error", "-ss", str(start), "-i", str(RAW / src), "-t", str(dur),
        "-filter_complex", fc, "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(out), "-y",
    ], check=True)


def build(key, spec):
    segs = []
    for i, (s, d) in enumerate(spec["windows"]):
        out = M / f"{key}_{i}.mp4"
        letterbox(spec["src"], s, d, spec["crop"], spec["bright"], spec["sat"], out)
        segs.append(out)
    listf = M / f"{key}.txt"
    listf.write_text("".join(f"file '{p.name}'\n" for p in segs), encoding="utf-8")
    vert = C / f"vert_{key}.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listf),
        "-c", "copy", str(vert), "-y",
    ], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(vert)], capture_output=True, text=True).stdout.strip()
    print(f"{key:12s} -> {vert.name}  {dur}s  ({len(segs)} segs)")


if __name__ == "__main__":
    for key, spec in SONGS.items():
        build(key, spec)
    print("done.")
