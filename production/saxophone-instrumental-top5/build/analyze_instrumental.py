#!/usr/bin/env python3
"""Analyze instrumental sources for strong phrase attacks and natural endings.

This is deliberately not a vocal detector.  It records audio-derived evidence
for the pure-instrumental gate and leaves the final musical-window decision
auditable in probe/instrumental_analysis.json.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import librosa
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
PROBE = ROOT / "probe"
SR = 22_050
HOP = 2_205  # 100 ms

SOURCES = {
    "p5": ("p5_mister_magic_yt.mp4", 125.0),
    "p4": ("p4_forever_in_love_bili.mp4", 82.0),
    "p3": ("p3_lily_was_here_bili.mp4", 88.0),
    "p2": ("p2_going_home_yt.mp4", 96.0),
    "p1": ("p1_songbird_bili.mp4", 84.0),
}


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def decode_mono(path: Path) -> np.ndarray:
    result = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
            "-ar", str(SR), "-f", "f32le", "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return np.frombuffer(result.stdout, dtype=np.float32)


def separated_top(times: np.ndarray, scores: np.ndarray, count: int = 24) -> list[dict[str, float]]:
    order = np.argsort(scores)[::-1]
    chosen: list[tuple[float, float]] = []
    for index in order:
        time = float(times[index])
        score = float(scores[index])
        if any(abs(time - previous) < 4.0 for previous, _ in chosen):
            continue
        chosen.append((time, score))
        if len(chosen) >= count:
            break
    return [
        {"time": round(time, 3), "onset_score": round(score, 4)}
        for time, score in sorted(chosen)
    ]


def quiet_boundaries(times: np.ndarray, rms_db: np.ndarray, onset: np.ndarray) -> list[dict[str, float]]:
    """Return separated local low-energy / low-onset cut candidates."""
    rms_norm = (rms_db - float(np.min(rms_db))) / max(1e-6, float(np.ptp(rms_db)))
    onset_norm = onset / max(1e-6, float(np.max(onset)))
    score = np.convolve(0.72 * rms_norm + 0.28 * onset_norm, np.ones(9) / 9, mode="same")
    candidates: list[int] = []
    for index in range(20, len(score) - 20):
        if times[index] < 12.0:
            continue
        window = score[index - 12:index + 13]
        if score[index] <= float(np.min(window)):
            candidates.append(index)
    order = sorted(candidates, key=lambda index: float(score[index]))
    chosen: list[int] = []
    for index in order:
        if any(abs(float(times[index] - times[previous])) < 4.0 for previous in chosen):
            continue
        chosen.append(index)
        if len(chosen) >= 36:
            break
    chosen.sort()
    return [
        {
            "time": round(float(times[index]), 3),
            "rms_dbfs": round(float(rms_db[index]), 2),
            "boundary_score": round(float(score[index]), 4),
        }
        for index in chosen
    ]


def analyze(key: str, filename: str, target_show: float) -> dict[str, object]:
    path = RAW / filename
    duration = probe_duration(path)
    y = decode_mono(path)

    rms = librosa.feature.rms(y=y, frame_length=4096, hop_length=HOP)[0]
    rms_db = librosa.amplitude_to_db(np.maximum(rms, 1e-9), ref=1.0)
    onset = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    frame_count = min(len(rms_db), len(onset))
    rms_db = rms_db[:frame_count]
    onset = onset[:frame_count]
    times = librosa.frames_to_time(np.arange(frame_count), sr=SR, hop_length=HOP)

    peak_frames = librosa.onset.onset_detect(
        onset_envelope=onset,
        sr=SR,
        hop_length=HOP,
        backtrack=True,
        units="frames",
    )
    peak_frames = peak_frames[peak_frames < frame_count]
    peak_times = times[peak_frames]
    peak_scores = onset[peak_frames]

    # Relative gate survives loud and quiet masters: audible means no more than
    # 32 dB below the 90th-percentile program level, with a -52 dBFS floor.
    program_db = float(np.percentile(rms_db, 90))
    audible_threshold = max(-52.0, program_db - 32.0)
    audible_frames = np.flatnonzero(rms_db >= audible_threshold)
    natural_end = float(times[audible_frames[-1]]) if len(audible_frames) else duration

    desired = natural_end - target_show
    near = np.flatnonzero((peak_times >= desired - 18.0) & (peak_times <= desired + 18.0))
    if len(near):
        chosen_frame = peak_frames[near[np.argmax(peak_scores[near])]]
    else:
        chosen_frame = int(np.argmin(np.abs(times - desired)))
    suggested_start = float(times[chosen_frame])

    tempo_value = librosa.feature.tempo(
        onset_envelope=onset, sr=SR, hop_length=HOP, aggregate=np.median
    )
    tempo = float(np.atleast_1d(tempo_value)[0])

    return {
        "key": key,
        "source": filename,
        "source_duration": round(duration, 3),
        "program_level_p90_dbfs": round(program_db, 2),
        "audible_threshold_dbfs": round(audible_threshold, 2),
        "natural_audible_end": round(natural_end, 3),
        "trailing_below_threshold": round(max(0.0, duration - natural_end), 3),
        "estimated_tempo_bpm": round(tempo, 2),
        "target_show_duration": target_show,
        "suggested_phrase_start": round(suggested_start, 3),
        "suggested_show_duration": round(natural_end - suggested_start, 3),
        "strong_attacks": separated_top(peak_times, peak_scores),
        "quiet_cut_candidates": quiet_boundaries(times, rms_db, onset),
        "evidence": "librosa onset-strength attack plus relative RMS natural-end gate",
    }


def main() -> None:
    PROBE.mkdir(parents=True, exist_ok=True)
    items = [analyze(key, filename, target) for key, (filename, target) in SOURCES.items()]
    payload = {"kind": "instrumental_phrase_analysis", "items": items}
    output = PROBE / "instrumental_analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in items:
        print(
            item["key"],
            "start", item["suggested_phrase_start"],
            "end", item["natural_audible_end"],
            "show", item["suggested_show_duration"],
            "tempo", item["estimated_tempo_bpm"],
        )
    print(output)


if __name__ == "__main__":
    main()
