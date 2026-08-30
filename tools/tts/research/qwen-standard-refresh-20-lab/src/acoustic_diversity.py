#!/usr/bin/env python3
"""Measure acoustic spread of the generated common-text listening samples."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path

import librosa
import numpy as np


LAB_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = LAB_ROOT / "manifest.json"
LISTEN_ROOT = LAB_ROOT / "outputs" / "listen-audio"
OUTPUT_PATH = LAB_ROOT / "outputs" / "qa" / "acoustic-diversity-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: np.ndarray, value: float) -> float | None:
    return float(np.percentile(values, value)) if values.size else None


def analyze(persona: dict) -> tuple[dict, np.ndarray]:
    path = LISTEN_ROOT / persona["id"] / "showcase.wav"
    audio, sample_rate = librosa.load(path, sr=24000, mono=True)
    f0, voiced_flag, _ = librosa.pyin(
        audio,
        fmin=librosa.note_to_hz("A1"),
        fmax=librosa.note_to_hz("C6"),
        sr=sample_rate,
        frame_length=1024,
        hop_length=256,
    )
    voiced = f0[np.isfinite(f0)]
    rms = librosa.feature.rms(y=audio, frame_length=1024, hop_length=256)[0]
    centroid = librosa.feature.spectral_centroid(
        y=audio, sr=sample_rate, n_fft=1024, hop_length=256
    )[0]
    onset = librosa.onset.onset_strength(y=audio, sr=sample_rate, hop_length=256)
    onset_count = len(
        librosa.onset.onset_detect(
            onset_envelope=onset, sr=sample_rate, hop_length=256, units="frames"
        )
    )
    mfcc = librosa.feature.mfcc(
        y=audio, sr=sample_rate, n_mfcc=13, n_fft=1024, hop_length=256
    )
    duration = len(audio) / sample_rate
    record = {
        "persona_id": persona["id"],
        "label": persona["label"],
        "group": persona["group"],
        "path": str(path.relative_to(LAB_ROOT)),
        "sha256": sha256(path),
        "duration_seconds": duration,
        "f0_median_hz": percentile(voiced, 50),
        "f0_p10_hz": percentile(voiced, 10),
        "f0_p90_hz": percentile(voiced, 90),
        "voiced_frame_ratio": float(np.mean(voiced_flag)) if voiced_flag.size else 0.0,
        "spectral_centroid_median_hz": percentile(centroid, 50),
        "rms_p10_db": percentile(librosa.amplitude_to_db(rms, ref=1.0), 10),
        "rms_p90_db": percentile(librosa.amplitude_to_db(rms, ref=1.0), 90),
        "onset_events_per_second": onset_count / duration,
    }
    feature = np.concatenate(
        [
            np.array(
                [
                    np.log(max(record["f0_median_hz"] or 1.0, 1.0)),
                    np.log(max(record["spectral_centroid_median_hz"] or 1.0, 1.0)),
                    duration,
                    record["voiced_frame_ratio"],
                    record["onset_events_per_second"],
                    (record["rms_p90_db"] or 0.0) - (record["rms_p10_db"] or 0.0),
                ]
            ),
            np.mean(mfcc, axis=1),
            np.std(mfcc, axis=1),
        ]
    )
    return record, feature


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    analyzed = [analyze(persona) for persona in manifest["personas"]]
    records = [item[0] for item in analyzed]
    features = np.stack([item[1] for item in analyzed])
    means = features.mean(axis=0)
    scales = features.std(axis=0)
    scales[scales < 1e-9] = 1.0
    standardized = (features - means) / scales
    distances = []
    for left, right in combinations(range(len(records)), 2):
        distances.append(
            {
                "left": records[left]["persona_id"],
                "right": records[right]["persona_id"],
                "standardized_feature_distance": float(
                    np.linalg.norm(standardized[left] - standardized[right])
                ),
            }
        )
    distances.sort(key=lambda item: item["standardized_feature_distance"])
    group_summary = {}
    for group in ("female", "male"):
        subset = [record for record in records if record["group"] == group]
        pitches = [record["f0_median_hz"] for record in subset if record["f0_median_hz"]]
        durations = [record["duration_seconds"] for record in subset]
        group_summary[group] = {
            "count": len(subset),
            "median_f0_min_hz": min(pitches),
            "median_f0_max_hz": max(pitches),
            "duration_min_seconds": min(durations),
            "duration_max_seconds": max(durations),
        }
    report = {
        "schema_version": "1.0.0",
        "experiment_id": manifest["experiment_id"],
        "interpretation": "Observed acoustic-feature spread for screening only; this is not a human judgment of naturalness, style identity, or suitability.",
        "records": records,
        "summary": {
            "voice_count": len(records),
            "unique_audio_hashes": len({record["sha256"] for record in records}),
            "group_summary": group_summary,
            "closest_feature_pair": distances[0],
            "median_pairwise_feature_distance": float(
                np.median([item["standardized_feature_distance"] for item in distances])
            ),
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"ACOUSTIC DIVERSITY: OBSERVED path={OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
