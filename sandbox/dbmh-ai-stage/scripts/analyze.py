#!/usr/bin/env python3
"""分析三段音频的 BPM、调性、能量段落，输出 audio_analysis.json"""
import json, sys
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

KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def analyze(name, path):
    y, sr = librosa.load(str(path), sr=SR, mono=True)
    dur = len(y) / sr

    # BPM + beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Key (粗略: chroma 平均最大值)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    pitch_class = int(np.argmax(chroma.mean(axis=1)))
    key = KEY_NAMES[pitch_class]

    # 段落能量 (每 5s 窗口的 RMS)
    win = 5
    hop = 2
    rms = []
    for t in np.arange(0, dur - win, hop):
        s = int(t * sr); e = int((t + win) * sr)
        rms.append({"t": round(float(t), 2), "rms_db": round(float(20*np.log10(np.sqrt(np.mean(y[s:e]**2)) + 1e-9)), 2)})

    # Onset strength (找强拍/段落入口)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.util.peak_pick(onset_env, pre_max=20, post_max=20, pre_avg=20, post_avg=20, delta=0.5, wait=20)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    # 取前 30 个最强 onset
    strong = sorted([(float(onset_env[f]), float(t)) for f, t in zip(onset_frames, onset_times)], reverse=True)[:30]
    strong_times = sorted([round(t, 2) for _, t in strong])

    return {
        "name": name,
        "duration": round(float(dur), 2),
        "bpm": round(float(np.asarray(tempo).flatten()[0]), 2),
        "key_estimate": key,
        "beat_count": int(len(beat_times)),
        "first_10_beats": [round(float(t), 3) for t in beat_times[:10]],
        "energy_windows": rms,
        "strong_onsets": strong_times,
    }

results = {}
for name, path in SOURCES.items():
    print(f"分析 {name}...", flush=True)
    results[name] = analyze(name, path)
    print(f"  duration={results[name]['duration']}s  bpm={results[name]['bpm']}  key={results[name]['key_estimate']}")

out = ROOT / "audio_analysis.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"写入 {out}")
