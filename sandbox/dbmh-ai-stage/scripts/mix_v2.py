#!/usr/bin/env python3
"""master.wav v2 — 真正的接力：窦唯 verse1 → 王菲 verse2 → 窦靖童 final chorus。
源时间码基于 vocal_analysis.json 的精细人声段检测。

主轨 174s:
  0-12     dw_床 (DW 65-77s) 低音量 + TTS intro
  12-50    DW verse1 (DW 77-115s, 38s)
  48-52    crossfade 4s (overlap fw 进)
  50-104   FW verse2+chorus (FW 130-184s, 54s)
  102-110  crossfade 8s (overlap jt 进)
  108-150  JT 桥+final chorus (JT 202-244s, 42s)
  150-164  threeway 短切 + stack
  164-174  jt_outro (JT 248-258s) + TTS outro
"""
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 44100

def load(path):
    data, file_sr = sf.read(str(path), always_2d=True)
    if data.shape[1] == 1:
        data = np.tile(data, (1, 2))
    if file_sr != SR:
        raise RuntimeError(f"sr mismatch {file_sr}")
    return data.astype(np.float32)

def slice_a(y, t0, t1):
    return y[int(t0*SR):int(t1*SR)]

def take(src_y, t0, t1, name, I=-16):
    """切 + loudnorm。"""
    y = slice_a(src_y, t0, t1)
    in_p = ROOT / "audio" / f"_in_{name}.wav"
    out_p = ROOT / "audio" / f"_ln_{name}.wav"
    sf.write(in_p, y, SR)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(in_p),
        "-af", f"loudnorm=I={I}:TP=-1.0:LRA=11",
        "-ar", str(SR), "-ac", "2", str(out_p)
    ], check=True)
    y2, _ = sf.read(str(out_p), always_2d=True)
    in_p.unlink(); out_p.unlink()
    return y2.astype(np.float32)

def fade(y, in_s=0, out_s=0):
    out = y.copy()
    n_in = int(in_s * SR)
    n_out = int(out_s * SR)
    if n_in > 0 and n_in <= len(out):
        out[:n_in] *= np.linspace(0, 1, n_in).reshape(-1, 1)
    if n_out > 0 and n_out <= len(out):
        out[-n_out:] *= np.linspace(1, 0, n_out).reshape(-1, 1)
    return out

print("加载源...")
DW = load(ROOT / "audio/douwei_heibao_full.wav")
FW = load(ROOT / "audio/faye_budokan_full.wav")
JT = load(ROOT / "audio/jingtong_singer2026_full.wav")

print("切片 + loudnorm...")
dw_bed   = take(DW, 65, 77,   "dw_bed")     # 12s intro 床（无人声）
dw_main  = take(DW, 77, 115,  "dw_main")    # 38s verse1
fw_in    = take(FW, 128, 134, "fw_in")      # 6s 进入段（含桥段尾 + verse2 起）
fw_main  = take(FW, 134, 188, "fw_main")    # 54s verse2 + chorus
jt_in    = take(JT, 198, 206, "jt_in")      # 8s 进入段（chorus 间隔伴奏）
jt_main  = take(JT, 206, 244, "jt_main")    # 38s pre-final + final chorus
# threeway 三人 14s (同 v1)
dw_three = take(DW, 70, 84,   "dw_three")
fw_three = take(FW, 213, 227, "fw_three")
jt_three = take(JT, 213, 227, "jt_three")
# stack3 - 取 final chorus 最后一句各 2s
dw_stk   = take(DW, 84, 86,   "dw_stk")
fw_stk   = take(FW, 224, 226, "fw_stk")
jt_stk   = take(JT, 224, 226, "jt_stk")
# outro
jt_outro = take(JT, 248, 258, "jt_outro")

print("拼合主轨 174s...")
TOTAL = 174
master = np.zeros((int(TOTAL*SR), 2), dtype=np.float32)

def mix_in(master, seg, t_start, gain_db=0):
    s = int(t_start * SR)
    e = min(s + len(seg), len(master))
    seg = seg[:e-s]
    master[s:e] += seg * (10 ** (gain_db / 20))

# 0-12s: dw_bed 床 (-8dB), TTS 叠加
seg = fade(dw_bed, in_s=0.3, out_s=0.5)
mix_in(master, seg, 0, gain_db=-8)

# 12-50s: dw_main verse1（衔接 dw_bed 末尾，源 77-115s 紧接 65-77s 自然连续）
seg = fade(dw_main, in_s=0.3, out_s=2.0)
mix_in(master, seg, 12)

# 48-54s: fw_in 6s 进入段，crossfade with dw_main 末 2s
seg = fade(fw_in, in_s=2.0, out_s=0.3)
mix_in(master, seg, 48)

# 54-108s: fw_main verse2+chorus 54s，与 fw_in 末 0.3s 微 crossfade
# fw_in 在源里是 128-134，fw_main 134-188，自然连续，无需 crossfade
seg = fade(fw_main, in_s=0.5, out_s=2.5)
mix_in(master, seg, 54)

# 106-114s: jt_in 8s 进入段，crossfade with fw_main 末 2s
seg = fade(jt_in, in_s=2.5, out_s=0.3)
mix_in(master, seg, 106)

# 114-152s: jt_main 38s final chorus，与 jt_in 自然连续（源 198-206 + 206-244）
seg = fade(jt_main, in_s=0.3, out_s=2.0)
mix_in(master, seg, 114)

# 150-152s: jt_main 末与 threeway 短切的 2s 重叠（让画面切换平滑）
# 152-156s: dw_three 4s
seg = fade(dw_three[:int(4*SR)], in_s=0.2, out_s=0.3)
mix_in(master, seg, 152)
# 156-160s: fw_three 4s
seg = fade(fw_three[:int(4*SR)], in_s=0.3, out_s=0.3)
mix_in(master, seg, 156)
# 160-164s: jt_three 4s
seg = fade(jt_three[:int(4*SR)], in_s=0.3, out_s=0.3)
mix_in(master, seg, 160)

# 三人 stack 162-164s（各 -6dB）— 与 jt_three 同段 overlap
seg = fade(dw_stk, in_s=0.1, out_s=0.5); mix_in(master, seg, 162, gain_db=-6)
seg = fade(fw_stk, in_s=0.1, out_s=0.5); mix_in(master, seg, 162, gain_db=-6)
seg = fade(jt_stk, in_s=0.1, out_s=0.5); mix_in(master, seg, 162, gain_db=-6)

# 164-174s: jt_outro 床 (-10dB) + TTS outro
seg = fade(jt_outro, in_s=0.5, out_s=4.0)
mix_in(master, seg, 164, gain_db=-10)

# ============ TTS 叠加 ============
print("叠加 TTS + ducking...")
tts_intro, ir = sf.read(str(ROOT / "voice/intro.wav"), always_2d=True)
tts_outro, or_ = sf.read(str(ROOT / "voice/outro.wav"), always_2d=True)
if tts_intro.shape[1] == 1: tts_intro = np.tile(tts_intro, (1, 2))
if tts_outro.shape[1] == 1: tts_outro = np.tile(tts_outro, (1, 2))

def to_44k(y, sr):
    if sr == SR: return y.astype(np.float32)
    import scipy.signal as ss
    n = int(len(y) * SR / sr)
    return ss.resample(y, n).astype(np.float32)
tts_intro = to_44k(tts_intro, ir)
tts_outro = to_44k(tts_outro, or_)

TTS_INTRO_START = 0.5
TTS_INTRO_END = TTS_INTRO_START + len(tts_intro)/SR
TTS_OUTRO_START = 165.0
TTS_OUTRO_END = TTS_OUTRO_START + len(tts_outro)/SR

def duck(master, t0, t1, attack=0.3, release=0.3, target_db=-12):
    s = int(t0 * SR); e = int(t1 * SR)
    factor = 10 ** (target_db / 20)
    n_a = int(attack * SR); n_r = int(release * SR)
    mid_s = s + n_a; mid_e = e - n_r
    if mid_e > mid_s:
        master[mid_s:mid_e] *= factor
    if n_a > 0:
        r = np.linspace(1, factor, n_a).reshape(-1, 1)
        master[s:mid_s] *= r
    if n_r > 0:
        r = np.linspace(factor, 1, n_r).reshape(-1, 1)
        master[mid_e:e] *= r

duck(master, TTS_INTRO_START - 0.2, TTS_INTRO_END + 0.5, target_db=-10)
duck(master, TTS_OUTRO_START - 0.2, TTS_OUTRO_END + 0.5, target_db=-12)

def add_tts(master, tts, t_start):
    s = int(t_start * SR)
    e = min(s + len(tts), len(master))
    master[s:e] += tts[:e-s]

add_tts(master, tts_intro, TTS_INTRO_START)
add_tts(master, tts_outro, TTS_OUTRO_START)

# limit
peak = np.abs(master).max()
print(f"peak before limit: {peak:.3f}")
if peak > 0.95:
    master *= 0.95 / peak

mp = ROOT / "master.wav"
sf.write(mp, master, SR)
print(f"写入 {mp}")

print("整体 loudnorm 到 -14 LUFS...")
fp = ROOT / "master_final.wav"
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", str(mp),
    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
    "-ar", str(SR), "-ac", "2", str(fp)
], check=True)
print(f"完成 {fp}")

# QA
print("\nQA:")
sil = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "info", "-i", str(fp),
                     "-af", "silencedetect=n=-35dB:d=1", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
sil_lines = [l for l in sil.split("\n") if "silence" in l.lower()]
if sil_lines:
    for l in sil_lines[:5]: print(" ", l)
else:
    print("  无 >1s 静音 ✓")

# 各段响度
for start, label in [(5,"intro+TTS"),(20,"DW verse1"),(40,"DW chorus入"),
                     (60,"FW verse2"),(80,"FW chorus"),(115,"JT入"),(130,"JT chorus"),
                     (152,"threeway"),(168,"outro+TTS")]:
    out = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "info", "-ss", str(start),
                          "-t", "5", "-i", str(fp), "-af", "volumedetect",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    m = re.search(r'mean_volume: *(-?[0-9.]+) dB', out)
    print(f"  t={start:3d}-{start+5:3d}  {label:18s}  mean={m.group(1) if m else '?':>6}dB")
