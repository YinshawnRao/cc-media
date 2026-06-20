#!/usr/bin/env python3
"""Analyze credible vocal high-note windows and suggest new clip starts."""
from __future__ import annotations

import json
import math
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
QA = ROOT / "qa"
AN = ROOT / "analysis"
AUDIO = AN / "audio"

SR = 22050
HOP = 512
LEAD = 0.35
DIG = 1.5
LEN = 62.0
SHOW_DEFAULT = 38.0
SHOW_MAP = {
    "p5_shiye": 32.0,
    "p4_juebieshi": 34.0,
    "p3_hongyan": 26.0,
}


@dataclass(frozen=True)
class Song:
    key: str
    plain: str
    raw: str
    crop: str


SONGS = [
    Song("p5_shiye", "失业情歌", "shiye_live_yt.mp4", "1280:620:0:20"),
    Song("p4_juebieshi", "诀别诗", "juebieshi_yt.mp4", "640:360:0:60"),
    Song("p3_hongyan", "红颜", "hongyan_yt.mp4", "1920:760:0:160"),
    Song("p2_yueguang", "月光", "yueguang_bili_live.mp4", "1920:620:0:120"),
    Song("p1_quannazou", "你要的全拿走", "quannazou_mv_yt.mp4", "1920:940:0:0"),
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        cwd=ROOT,
        text=True,
    ).strip()
    return float(out)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / f.getframerate()


def extract_audio(song: Song) -> Path:
    AUDIO.mkdir(parents=True, exist_ok=True)
    out = AUDIO / f"{song.key}.wav"
    src = RAW / song.raw
    if not out.exists():
        run(["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", str(SR), out.name, "-y"])
        # ffmpeg wrote in ROOT; move into analysis/audio without shell redirects.
        (ROOT / out.name).replace(out)
    return out


def note_name(hz: float) -> str:
    if not hz or math.isnan(hz):
        return ""
    midi = int(round(69 + 12 * math.log2(hz / 440.0)))
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[midi % 12]}{midi // 12 - 1}"


def contiguous_segments(active: np.ndarray, times: np.ndarray, min_dur: float = 2.0, gap_tol: float = 1.2) -> list[tuple[float, float]]:
    segments: list[tuple[float, float]] = []
    in_seg = False
    start = 0.0
    last = 0.0
    for t, a in zip(times, active):
        if a:
            if not in_seg:
                start = float(t)
                in_seg = True
            last = float(t)
        elif in_seg and (float(t) - last) > gap_tol:
            if last - start >= min_dur:
                segments.append((round(start, 2), round(last, 2)))
            in_seg = False
    if in_seg and last - start >= min_dur:
        segments.append((round(start, 2), round(last, 2)))
    return segments


def coverage(active: np.ndarray, times: np.ndarray, start: float, end: float) -> float:
    mask = (times >= start) & (times <= end)
    if not np.any(mask):
        return 0.0
    return float(np.mean(active[mask]))


def analyze_song(song: Song, voice_dur: float) -> dict:
    audio = extract_audio(song)
    y, sr = librosa.load(str(audio), sr=SR, mono=True)
    duration = len(y) / sr

    y_harm, _ = librosa.effects.hpss(y, margin=3.0)
    stft = np.abs(librosa.stft(y_harm, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    voice_mask = (freqs >= 180) & (freqs <= 3200)
    voice_rms = np.sqrt(np.mean(stft[voice_mask, :] ** 2, axis=0))
    times = librosa.frames_to_time(np.arange(len(voice_rms)), sr=sr, hop_length=HOP)
    smooth_n = max(3, int(0.8 / (times[1] - times[0])))
    voice_smooth = np.convolve(voice_rms, np.ones(smooth_n) / smooth_n, mode="same")
    active_thresh = np.percentile(voice_smooth, 58)
    active = voice_smooth > active_thresh

    # Keep the estimator in a realistic male-singing range. A wider fmax produced
    # octave errors on old/live mixes where cymbals or synths dominate the top end.
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C5"),
        sr=sr,
        frame_length=2048,
        hop_length=HOP,
    )
    n = min(len(times), len(f0), len(voiced_prob), len(active))
    times = times[:n]
    active = active[:n]
    f0 = f0[:n]
    voiced_prob = voiced_prob[:n]

    credible = (~np.isnan(f0)) & (voiced_prob >= 0.48) & active
    if not np.any(credible):
        raise RuntimeError(f"No credible vocal f0 frames for {song.key}")

    # Rank by high but stable vocal pitches. Single-frame spikes are ignored by clustering.
    high_thresh = max(np.nanpercentile(f0[credible], 84), 245.0)
    high_active = credible & (f0 >= high_thresh)
    high_groups = contiguous_segments(high_active, times, min_dur=0.14, gap_tol=0.42)
    vocal_segments = contiguous_segments(active, times, min_dur=2.0, gap_tol=1.4)

    if not high_groups:
        # Short melisma/high-note peaks may not stay above threshold long enough
        # to form a normal cluster. Fall back to local groups around top f0 frames.
        top = np.argsort(np.nan_to_num(f0) * credible)[-24:][::-1]
        fallback = []
        for idx in top:
            if not credible[idx]:
                continue
            t = float(times[idx])
            group = (round(max(0.0, t - 0.22), 2), round(min(duration, t + 0.22), 2))
            if all(abs(group[0] - old[0]) > 1.0 for old in fallback):
                fallback.append(group)
            if len(fallback) >= 8:
                break
        high_groups = fallback

    narr_end_local = LEAD + voice_dur
    full_start_local = narr_end_local + 0.25 + DIG
    show = SHOW_MAP.get(song.key, SHOW_DEFAULT)
    raw_dur = ffprobe_duration(RAW / song.raw)

    candidates = []
    for gs, ge in high_groups:
        mask = (times >= gs) & (times <= ge) & credible
        if not np.any(mask):
            continue
        group_f0 = f0[mask]
        group_times = times[mask]
        peak_idx = int(np.nanargmax(group_f0))
        peak_time = float(group_times[peak_idx])
        peak_hz = float(group_f0[peak_idx])
        seg = next(((s, e) for s, e in vocal_segments if s - 0.25 <= peak_time <= e + 0.25), (max(0.0, peak_time - 8), min(duration, peak_time + 8)))

        target_peak_local = full_start_local + min(9.0, show * 0.34)
        base_start = peak_time - target_peak_local
        best = None
        # Search local start offsets so the selected high phrase stays inside the post-narration showcase
        # and the showcase itself is mostly vocal, not instrumental.
        for delta in np.arange(-12.0, 12.01, 0.5):
            start = max(0.0, min(raw_dur - LEN - 0.05, base_start + float(delta)))
            show_s = start + full_start_local
            show_e = show_s + show
            if not (show_s <= peak_time <= show_e):
                continue
            cov = coverage(active, times, show_s, show_e)
            first_cov = coverage(active, times, show_s, min(show_e, show_s + 8.0))
            phrase_s = max(seg[0], show_s - 2.0)
            phrase_e = min(seg[1], show_e)
            phrase_cov = coverage(active, times, phrase_s, phrase_e)
            peak_pos = (peak_time - show_s) / max(1.0, show)
            pos_score = 1.0 - min(1.0, abs(peak_pos - 0.32) / 0.32)
            # Vocal coverage matters more than absolute pitch: a slightly lower
            # but continuous sung phrase is preferable to a one-frame high spike.
            score = cov * 2.8 + first_cov * 0.9 + phrase_cov * 0.6 + pos_score * 0.35 + min(1.0, peak_hz / 520.0) * 0.25
            trial = {
                "clip_start": round(start, 2),
                "show_source_start": round(show_s, 2),
                "show_source_end": round(show_e, 2),
                "show_vocal_coverage": round(cov, 3),
                "first8_vocal_coverage": round(first_cov, 3),
                "score": round(score, 4),
            }
            if best is None or trial["score"] > best["score"]:
                best = trial
        if not best:
            continue
        candidates.append(
            {
                "peak_time": round(peak_time, 2),
                "peak_hz": round(peak_hz, 1),
                "peak_note": note_name(peak_hz),
                "high_group": [round(gs, 2), round(ge, 2)],
                "vocal_segment": [round(seg[0], 2), round(seg[1], 2)],
                **best,
            }
        )

    candidates.sort(key=lambda c: (c["score"], c["peak_hz"], c["show_vocal_coverage"]), reverse=True)
    selected = candidates[0]
    return {
        "key": song.key,
        "plain": song.plain,
        "raw": song.raw,
        "crop": song.crop,
        "raw_duration": round(raw_dur, 2),
        "voice_dur": round(voice_dur, 3),
        "narr_end_local": round(narr_end_local, 3),
        "full_start_local": round(full_start_local, 3),
        "show": show,
        "vocal_segments": vocal_segments,
        "selected": selected,
        "top_candidates": candidates[:8],
    }


def main() -> None:
    QA.mkdir(parents=True, exist_ok=True)
    meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
    results = {}
    for song in SONGS:
        print(f"=== {song.plain} ===", flush=True)
        result = analyze_song(song, float(meta[song.key]["dur"]))
        sel = result["selected"]
        print(
            f"selected peak={sel['peak_time']}s {sel['peak_note']} {sel['peak_hz']}Hz "
            f"clip_start={sel['clip_start']} show={sel['show_source_start']}-{sel['show_source_end']} "
            f"coverage={sel['show_vocal_coverage']}",
            flush=True,
        )
        results[song.key] = result

    out = QA / "high_note_analysis.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# High-note analysis", ""]
    for result in results.values():
        sel = result["selected"]
        lines.append(f"## {result['plain']}")
        lines.append(f"- peak: {sel['peak_time']}s / {sel['peak_note']} / {sel['peak_hz']}Hz")
        lines.append(f"- vocal segment: {sel['vocal_segment'][0]}-{sel['vocal_segment'][1]}s")
        lines.append(f"- clip_start: {sel['clip_start']}s")
        lines.append(f"- full-music source window: {sel['show_source_start']}-{sel['show_source_end']}s")
        lines.append(f"- vocal coverage: {sel['show_vocal_coverage']} / first8 {sel['first8_vocal_coverage']}")
        lines.append("")
    (QA / "high_note_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
