#!/usr/bin/env python3
"""人声段落精细检测：
1. 谐波分离拿 vocal-like signal
2. 1s 窗口 RMS 找 vocal onset / segment boundaries
3. 自相似矩阵找 chorus 重复模式（chorus 在歌中重复 2-3 次）
输出每段的：vocal_onsets（人声段起止 list），chorus_candidates（疑似副歌段）。
"""
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

def analyze(name, path):
    y, sr = librosa.load(str(path), sr=SR, mono=True)
    dur = len(y) / sr

    # 谐波-冲击分离
    y_harm, y_perc = librosa.effects.hpss(y, margin=3.0)

    # vocal-band（人声）能量：200-3000 Hz
    S_harm = np.abs(librosa.stft(y_harm, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    voice_mask = (freqs >= 200) & (freqs <= 3000)
    voice_rms = np.sqrt(np.mean(S_harm[voice_mask, :] ** 2, axis=0))
    times = librosa.frames_to_time(np.arange(len(voice_rms)), sr=sr, hop_length=512)

    # 平滑到 1s 窗口
    win = int(1.0 / (times[1] - times[0]))
    smoothed = np.convolve(voice_rms, np.ones(win) / win, mode='same')

    # vocal threshold: 取 60th percentile 作为有声/无声分界
    thresh = np.percentile(smoothed, 60)
    vocal_active = smoothed > thresh

    # 找 vocal 段（连续 vocal_active > 2s 视为有效 vocal 段）
    vocal_segments = []
    in_seg = False
    seg_start = 0
    min_dur = 2.0  # 至少 2s 才算 vocal 段
    gap_tol = 1.5  # 1.5s 内的 gap 视为同段
    last_active_t = None
    for i, active in enumerate(vocal_active):
        t = times[i]
        if active:
            if not in_seg:
                seg_start = t
                in_seg = True
            last_active_t = t
        else:
            if in_seg and (t - last_active_t) > gap_tol:
                seg_end = last_active_t
                if seg_end - seg_start >= min_dur:
                    vocal_segments.append([round(seg_start, 2), round(seg_end, 2)])
                in_seg = False
    if in_seg:
        seg_end = last_active_t if last_active_t else times[-1]
        if seg_end - seg_start >= min_dur:
            vocal_segments.append([round(seg_start, 2), round(seg_end, 2)])

    # 找 chorus: chroma 自相似找重复
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    rec = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True, width=11)
    # 沿对角线求平均得到 chorus 重复模式估计
    chroma_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=2048)

    # 取 RMS 高的段作为 chorus 候选（chorus 通常能量更高）
    rms_overall = librosa.feature.rms(y=y, hop_length=2048)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms_overall)), sr=sr, hop_length=2048)
    # 与 vocal_segments 交叉
    chorus_candidates = []
    for seg_start, seg_end in vocal_segments:
        mask = (rms_times >= seg_start) & (rms_times <= seg_end)
        if mask.sum() > 0:
            avg_rms = float(rms_overall[mask].mean())
            chorus_candidates.append({
                "start": seg_start, "end": seg_end,
                "duration": round(seg_end - seg_start, 2),
                "avg_rms": round(avg_rms, 4)
            })

    # 按 RMS 降序
    chorus_candidates_sorted = sorted(chorus_candidates, key=lambda c: -c["avg_rms"])

    return {
        "name": name,
        "duration": round(dur, 2),
        "vocal_segments": vocal_segments,
        "chorus_candidates_by_energy": chorus_candidates_sorted[:5],
    }

results = {}
for name, path in SOURCES.items():
    print(f"分析 {name}...", flush=True)
    results[name] = analyze(name, path)
    s = results[name]
    print(f"  vocal_segments ({len(s['vocal_segments'])}):", s['vocal_segments'])

out = ROOT / "vocal_analysis.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"\n写入 {out}")
