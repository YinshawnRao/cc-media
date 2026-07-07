#!/usr/bin/env python3
"""Heuristic chorus-region finder: smoothed RMS-dB envelope (8s moving avg),
reports the loudest sustained plateaus >= min_dur seconds as chorus candidates.
Not a substitute for human ears -- used to narrow down where to probe.
"""
import sys
import numpy as np
import librosa

def analyze(path, min_dur=24.0, win=1.0, smooth_s=8.0, pct=60):
    y, sr = librosa.load(path, sr=22050, mono=True)
    dur = len(y) / sr
    hop = int(win * sr)
    frames = []
    for i in range(0, len(y) - hop, hop):
        frames.append(np.sqrt(np.mean(y[i:i+hop]**2)))
    frames = np.array(frames)
    db = 20 * np.log10(frames + 1e-6)
    k = max(1, int(smooth_s / win))
    kernel = np.ones(k) / k
    smoothed = np.convolve(db, kernel, mode='same')
    times = np.arange(len(smoothed)) * win

    thresh = np.percentile(smoothed, pct)
    active = smoothed > thresh

    segs = []
    i = 0
    n = len(active)
    while i < n:
        if active[i]:
            j = i
            while j < n and active[j]:
                j += 1
            seg_start = times[i]
            seg_end = times[min(j, n-1)]
            if seg_end - seg_start >= min_dur:
                mean_db = smoothed[i:j].mean()
                segs.append((seg_start, seg_end, mean_db))
            i = j
        else:
            i += 1

    segs.sort(key=lambda s: -s[2])
    print(f"duration={dur:.1f}s  threshold(db)={thresh:.1f}")
    for s in segs[:8]:
        print(f"  candidate {s[0]:7.1f} - {s[1]:7.1f}  ({s[1]-s[0]:.1f}s)  mean_db={s[2]:.1f}")
    return segs

if __name__ == "__main__":
    pct = 60
    args = sys.argv[1:]
    if args and args[0].startswith("--pct="):
        pct = float(args[0].split("=")[1])
        args = args[1:]
    for p in args:
        print(f"=== {p} ===")
        analyze(p, pct=pct)
