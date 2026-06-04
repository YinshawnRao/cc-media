#!/usr/bin/env python3
"""构建 master.wav：三段音乐接力 + TTS intro/outro + ducking。
全部用 numpy 处理（不依赖复杂 ffmpeg filtergraph），输出 44.1kHz 立体声 wav。

时间轴（总 174s）：
  0-12      tts intro + douwei 5-17s 床 (-8dB)
  12-50     douwei 17-55s
  48-60     [overlap 2s] faye 63-77s 接入（前 1s 渐显，与窦唯 48-49 渐隐交叠）
  60-110    faye 77-127s 核心
 108-120    [overlap 2s] jingtong 31-45s 接入
 120-150    jingtong 45-75s
 150-164    threeway (DW 200-204 / FW 220-224 / JT 215-219，4s+4s+4s+2s 叠加)
 164-174    jingtong 245-255s 床 (-10dB) + tts outro
"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SR = 44100

def load(path, sr=SR):
    """读 wav，转 mono 或 stereo (这里统一 stereo)。"""
    data, file_sr = sf.read(str(path), always_2d=True)
    if data.shape[1] == 1:
        data = np.tile(data, (1, 2))
    if file_sr != sr:
        # ffmpeg resample
        tmp = path.with_suffix(".rs.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(path), "-ar", str(sr), "-ac", "2",
                        str(tmp)], check=True)
        data, _ = sf.read(str(tmp), always_2d=True)
        tmp.unlink()
    return data.astype(np.float32)

def gain_db(x, db):
    return x * (10 ** (db / 20))

def slice_audio(y, t0, t1, sr=SR):
    s = int(t0 * sr); e = int(t1 * sr)
    return y[s:e]

def loudnorm(in_path, out_path, I=-16, TP=-1.0, LRA=11):
    """单 pass loudnorm，目标响度 I dB。"""
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(in_path),
        "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}",
        "-ar", str(SR), "-ac", "2",
        str(out_path)
    ], check=True)

def write_seg(name, y):
    p = ROOT / "audio" / f"_seg_{name}.wav"
    sf.write(p, y, SR)
    return p

def fade(y, in_s=0, out_s=0, sr=SR):
    out = y.copy()
    n_in = int(in_s * sr)
    n_out = int(out_s * sr)
    if n_in > 0 and n_in <= len(out):
        ramp = np.linspace(0, 1, n_in).reshape(-1, 1)
        out[:n_in] *= ramp
    if n_out > 0 and n_out <= len(out):
        ramp = np.linspace(1, 0, n_out).reshape(-1, 1)
        out[-n_out:] *= ramp
    return out

# ============== 加载源 ==============
print("加载源 wav...")
DW = load(ROOT / "audio/douwei_heibao_full.wav")
FW = load(ROOT / "audio/faye_budokan_full.wav")
JT = load(ROOT / "audio/jingtong_singer2026_full.wav")
print(f"  DW {len(DW)/SR:.2f}s  FW {len(FW)/SR:.2f}s  JT {len(JT)/SR:.2f}s")

# ============== 切片并先做 loudnorm 各段 ==============
def take(src, t0, t1, name):
    y = slice_audio(src, t0, t1)
    in_p = ROOT / "audio" / f"_in_{name}.wav"
    out_p = ROOT / "audio" / f"_ln_{name}.wav"
    sf.write(in_p, y, SR)
    loudnorm(in_p, out_p, I=-16)
    y2, _ = sf.read(str(out_p), always_2d=True)
    in_p.unlink(); out_p.unlink()
    return y2.astype(np.float32)

print("切片 + loudnorm...")
dw_intro  = take(DW, 5, 17,   "dw_intro")    # 12s for tts床
dw_main   = take(DW, 17, 55,  "dw_main")     # 38s 主段 (主轨 12-50s, 48-50s 与 fw_in crossfade)
fw_in     = take(FW, 65, 77,  "fw_in")       # 12s 接入
fw_main   = take(FW, 77, 127, "fw_main")     # 50s 核心
jt_in     = take(JT, 33, 45,  "jt_in")       # 12s 接入
jt_main   = take(JT, 45, 75,  "jt_main")     # 30s 主段
# threeway 短切
dw_3      = take(DW, 200, 204, "dw_3")       # 4s
fw_3      = take(FW, 220, 224, "fw_3")       # 4s
jt_3      = take(JT, 215, 219, "jt_3")       # 4s
# stack3：三人同时 (各 -6dB) — 用 224-226 / 219-221 区段
dw_stk    = take(DW, 204, 206, "dw_stk")     # 2s
fw_stk    = take(FW, 224, 226, "fw_stk")     # 2s
jt_stk    = take(JT, 219, 221, "jt_stk")     # 2s
jt_outro  = take(JT, 245, 255, "jt_outro")   # 10s 床

# ============== 构建主轨 ==============
TOTAL = 174
total_samples = int(TOTAL * SR)
master = np.zeros((total_samples, 2), dtype=np.float32)

def mix_in(master, seg, t_start, gain_db_val=0):
    s = int(t_start * SR)
    e = s + len(seg)
    if e > len(master):
        seg = seg[:len(master) - s]
        e = s + len(seg)
    master[s:e] += seg * (10 ** (gain_db_val / 20))

print("拼合主轨...")
# 0-12s: dw_intro 床 (-8dB)，tts 段会再叠加
seg = fade(dw_intro, in_s=0.3, out_s=0)
mix_in(master, seg, 0, gain_db_val=-8)

# 12-50s: dw_main，但 12s 处接 dw_intro 末尾(17s处)→ dw_main 起点(17s) 自然连续，做 0.3s 渐显
# 同时 dw_intro 在 11s-12s 已经做了渐显（前面 in_s=0.3）但末尾应该渐隐到 dw_main 起点平滑过渡
# 这里 dw_intro 的 11.7-12s 与 dw_main 0-0.3s 实际上是源里 16.7-17s vs 17-17.3s，自然连续，无需 crossfade
seg = fade(dw_main, in_s=0.3, out_s=2.0)
mix_in(master, seg, 12)

# 48-60s: fw_in，与 dw_main 末尾(48-50s) crossfade 2s
# dw_main 已 fade_out 1s 在 49-50s 内（48-50 慢慢降，49 -> 0）
# fw_in 在 48s 开始 fade_in 2s
seg = fade(fw_in, in_s=2.0, out_s=0.3)
mix_in(master, seg, 48)

# 60-110s: fw_main
seg = fade(fw_main, in_s=0.3, out_s=1.0)
mix_in(master, seg, 60)

# 108-120s: jt_in，与 fw_main 末尾 2s crossfade
seg = fade(jt_in, in_s=2.0, out_s=0.3)
mix_in(master, seg, 108)

# 120-150s: jt_main
seg = fade(jt_main, in_s=0.3, out_s=0.5)
mix_in(master, seg, 120)

# 150-162s: threeway 短切 — DW 4s / FW 4s / JT 4s
seg = fade(dw_3, in_s=0.2, out_s=0.2); mix_in(master, seg, 150)
seg = fade(fw_3, in_s=0.2, out_s=0.2); mix_in(master, seg, 154)
seg = fade(jt_3, in_s=0.2, out_s=0.2); mix_in(master, seg, 158)
# 162-164s: stack3 三人叠加 各 -6dB
seg = fade(dw_stk, in_s=0.1, out_s=0.5); mix_in(master, seg, 162, gain_db_val=-6)
seg = fade(fw_stk, in_s=0.1, out_s=0.5); mix_in(master, seg, 162, gain_db_val=-6)
seg = fade(jt_stk, in_s=0.1, out_s=0.5); mix_in(master, seg, 162, gain_db_val=-6)

# 164-174s: jt_outro 床 (-10dB) + tts outro
seg = fade(jt_outro, in_s=0.5, out_s=4.0)
mix_in(master, seg, 164, gain_db_val=-10)

# ============== TTS 叠加（带 ducking）==============
print("叠加 TTS + ducking...")
tts_intro, ir = sf.read(str(ROOT / "voice/intro.wav"), always_2d=True)
tts_outro, or_ = sf.read(str(ROOT / "voice/outro.wav"), always_2d=True)
# 转 stereo
if tts_intro.shape[1] == 1: tts_intro = np.tile(tts_intro, (1, 2))
if tts_outro.shape[1] == 1: tts_outro = np.tile(tts_outro, (1, 2))
# resample if needed
def to_44k(y, sr):
    if sr == SR: return y.astype(np.float32)
    import scipy.signal as ss
    n = int(len(y) * SR / sr)
    return ss.resample(y, n).astype(np.float32)
tts_intro = to_44k(tts_intro, ir)
tts_outro = to_44k(tts_outro, or_)

# intro: 0.5s 起，音量 +0dB
TTS_INTRO_START = 0.5
TTS_INTRO_END = TTS_INTRO_START + len(tts_intro)/SR
# outro: 165s 起，音量 +0dB
TTS_OUTRO_START = 165.0
TTS_OUTRO_END = TTS_OUTRO_START + len(tts_outro)/SR

# 把这两段 TTS 期间，master 的音乐降低到 -12dB（线性减增）
def duck(master, t0, t1, attack=0.3, release=0.3, target_db=-12):
    s = int(t0 * SR)
    e = int(t1 * SR)
    factor = 10 ** (target_db / 20)
    n_attack = int(attack * SR)
    n_release = int(release * SR)
    # 中间整段乘 factor
    mid_s = s + n_attack
    mid_e = e - n_release
    if mid_e > mid_s:
        master[mid_s:mid_e] *= factor
    # attack ramp 1 -> factor
    if n_attack > 0:
        r = np.linspace(1, factor, n_attack).reshape(-1, 1)
        master[s:mid_s] *= r
    # release ramp factor -> 1
    if n_release > 0:
        r = np.linspace(factor, 1, n_release).reshape(-1, 1)
        master[mid_e:e] *= r

duck(master, TTS_INTRO_START - 0.2, TTS_INTRO_END + 0.5, target_db=-10)
duck(master, TTS_OUTRO_START - 0.2, TTS_OUTRO_END + 0.5, target_db=-12)

# 加 TTS
def add_tts(master, tts, t_start, gain_db_val=0):
    s = int(t_start * SR)
    e = s + len(tts)
    if e > len(master):
        tts = tts[:len(master) - s]
        e = s + len(tts)
    master[s:e] += tts * (10 ** (gain_db_val / 20))

add_tts(master, tts_intro, TTS_INTRO_START, gain_db_val=0)
add_tts(master, tts_outro, TTS_OUTRO_START, gain_db_val=0)

# ============== 限峰避免 clipping ==============
peak = np.abs(master).max()
print(f"  peak before limit: {peak:.3f}")
if peak > 0.95:
    master *= 0.95 / peak
    print(f"  normalized to 0.95 peak")

# ============== 写出 master.wav ==============
master_path = ROOT / "master.wav"
sf.write(master_path, master, SR)
print(f"写入 {master_path} ({TOTAL}s)")

# ============== 跑一遍 loudnorm 第二阶段统一响度 ==============
final_path = ROOT / "master_final.wav"
print("整体 loudnorm 到 -14 LUFS...")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", str(master_path),
    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
    "-ar", str(SR), "-ac", "2",
    str(final_path)
], check=True)
print(f"完成 {final_path}")

# QA: 静音 + 响度
print("\nQA:")
subprocess.run(["ffmpeg", "-loglevel", "info", "-i", str(final_path),
                "-af", "silencedetect=n=-35dB:d=0.5,volumedetect",
                "-f", "null", "-"], stderr=subprocess.STDOUT)
