#!/usr/bin/env python3
"""更精细分析：每首歌的歌曲结构（intro/verse/chorus）边界。
方法：用 chroma 自相似矩阵 + agglomerative 找 N 段，配 RMS 能量曲线。
输出每段 BPM、beat 时间、能量曲线（2s 窗口）。"""
import json
from pathlib import Path
import numpy as np
import librosa

SR = 22050
ROOT = Path(__file__).resolve().parent.parent

SOURCES = {
    "douwei":   ROOT / "audio/douwei_heibao_full.wav",
    "faye":     ROOT / "audio/faye_budokan_full.wav",
    "jingtong": ROOT / "audio/jingtong_singer2026_full.wav",
}

def detailed(name, path):
    y, sr = librosa.load(str(path), sr=SR, mono=True)
    dur = len(y) / sr

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    bpm = float(np.asarray(tempo).flatten()[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # 2s 窗口 RMS（更细的能量曲线）
    hop = 1.0
    win = 2.0
    energy = []
    for t in np.arange(0, dur - win, hop):
        s = int(t * sr); e = int((t + win) * sr)
        rms_db = float(20*np.log10(np.sqrt(np.mean(y[s:e]**2)) + 1e-9))
        energy.append([round(float(t), 1), round(rms_db, 2)])

    # 简单段落检测：对 chroma 做 agglomerative
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    bounds = librosa.segment.agglomerative(chroma, 10)
    bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=2048).tolist()

    return {
        "name": name,
        "duration": round(dur, 2),
        "bpm": round(bpm, 2),
        "beat_times": [round(t, 3) for t in beat_times],
        "energy": energy,
        "segment_bounds": [round(t, 2) for t in bound_times],
    }

results = {}
for name, path in SOURCES.items():
    print(f"分析 {name}...", flush=True)
    results[name] = detailed(name, path)
    s = results[name]
    print(f"  dur={s['duration']}s bpm={s['bpm']} beats={len(s['beat_times'])} segments={s['segment_bounds']}")

out = ROOT / "audio_structure.json"
out.write_text(json.dumps(results, ensure_ascii=False))
print(f"写入 {out}")
