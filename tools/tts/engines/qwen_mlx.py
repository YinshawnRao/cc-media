#!/usr/bin/env python3
"""Offline Qwen3-TTS Base worker. Run only with the configured MLX interpreter."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = TTS_ROOT / "config.json"
REGISTRY_PATH = TTS_ROOT / "voices" / "registry.json"
sys.path.insert(0, str(TTS_ROOT))

from model_provenance import (  # noqa: E402
    ProvenanceError,
    manifest_path,
    model_candidates,
    validate_receipt,
)
from qwen_contract import (  # noqa: E402
    derived_seed,
    fingerprint,
    fingerprint_inputs,
    model_validation_cache_matches,
)


def bootstrap_offline_runtime() -> None:
    runtime = TTS_ROOT / "runtime" / "qwen-mlx"
    paths = {
        "HF_HOME": runtime / "hf",
        "HF_HUB_CACHE": runtime / "hf" / "hub",
        "HUGGINGFACE_HUB_CACHE": runtime / "hf" / "hub",
        "HF_XET_CACHE": runtime / "hf" / "xet",
        "TRANSFORMERS_CACHE": runtime / "transformers",
        "XDG_CACHE_HOME": runtime / "xdg-cache",
        "XDG_CONFIG_HOME": runtime / "xdg-config",
        "XDG_DATA_HOME": runtime / "xdg-data",
        "TMPDIR": runtime / "tmp",
        "TMP": runtime / "tmp",
        "TEMP": runtime / "tmp",
        "PYTHONPYCACHEPREFIX": runtime / "python-cache",
    }
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "TRANSFORMERS_NO_ADVISORY_WARNINGS": "1",
            "DO_NOT_TRACK": "1",
            "DISABLE_TELEMETRY": "1",
            "WANDB_DISABLED": "true",
            "TOKENIZERS_PARALLELISM": "false",
        }
    )


bootstrap_offline_runtime()

import mlx.core as mx  # noqa: E402
import numpy as np  # noqa: E402
from mlx_audio.audio_io import write as audio_write  # noqa: E402
from mlx_audio.tts.utils import load_model  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def installed_mlx_audio_version() -> str:
    try:
        return importlib.metadata.version("mlx-audio")
    except importlib.metadata.PackageNotFoundError as exc:
        raise SystemExit("mlx-audio distribution metadata is unavailable") from exc


def resolve_verified_model(config: dict, mlx_audio_version: str) -> tuple[Path, dict]:
    qwen = config["qwen_base"]
    if mlx_audio_version != qwen["mlx_audio_version"]:
        raise SystemExit(
            "mlx-audio version mismatch: "
            f"expected {qwen['mlx_audio_version']}, got {mlx_audio_version}"
        )
    try:
        source_manifest = manifest_path(config, TTS_ROOT)
    except ProvenanceError as exc:
        raise SystemExit(f"invalid pinned Qwen provenance configuration: {exc}") from exc
    rejected: list[str] = []
    for candidate in model_candidates(config, TTS_ROOT):
        if not candidate.is_dir():
            rejected.append(f"{candidate} (missing directory)")
            continue
        try:
            validation = validate_receipt(
                model_root=candidate,
                manifest_file=source_manifest,
                qwen=qwen,
                mlx_audio_version=mlx_audio_version,
                tts_root=TTS_ROOT,
            )
        except (OSError, ProvenanceError) as exc:
            rejected.append(f"{candidate} ({exc})")
            continue
        return candidate.resolve(), validation
    rendered = "\n  - ".join(rejected)
    raise SystemExit(
        "Qwen Base model lacks a current trusted full-hash verification; "
        "refusing to generate or fall back to Kokoro. Checked:\n"
        f"  - {rendered}\n"
        "Run `python3 tools/tts/doctor.py --full-model-hash` for the pinned model."
    )


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    mx.random.seed(seed)


def flatten_audio(results: list) -> tuple[np.ndarray, int, list[dict]]:
    if not results:
        raise RuntimeError("model returned no audio")
    sample_rates = {int(item.sample_rate) for item in results}
    if len(sample_rates) != 1:
        raise RuntimeError(f"model returned mixed sample rates: {sorted(sample_rates)}")
    arrays = [np.asarray(item.audio, dtype=np.float32).reshape(-1) for item in results]
    audio = arrays[0] if len(arrays) == 1 else np.concatenate(arrays)
    metrics = [
        {
            "processing_seconds": getattr(item, "processing_time_seconds", None),
            "peak_memory_gb": getattr(item, "peak_memory_usage", None),
            "token_count": getattr(item, "token_count", None),
        }
        for item in results
    ]
    return audio, sample_rates.pop(), metrics


def trim_edges(
    audio: np.ndarray, sample_rate: int, threshold_dbfs: float, padding_ms: int
) -> np.ndarray:
    frame_size = max(1, int(sample_rate * 0.02))
    frame_count = (len(audio) + frame_size - 1) // frame_size
    padded = np.pad(audio, (0, frame_count * frame_size - len(audio)))
    rms = np.sqrt(np.mean(padded.reshape(frame_count, frame_size) ** 2, axis=1))
    active = np.flatnonzero(rms >= 10 ** (threshold_dbfs / 20.0))
    if not len(active):
        raise RuntimeError("generated audio contains no audible samples")
    pad = int(sample_rate * padding_ms / 1000)
    start = max(0, int(active[0] * frame_size) - pad)
    end = min(len(audio), int((active[-1] + 1) * frame_size) + pad)
    return audio[start:end]


def wav_info(path: Path) -> dict:
    with wave.open(str(path), "rb") as handle:
        return {
            "channels": handle.getnchannels(),
            "sample_rate_hz": handle.getframerate(),
            "sample_width_bytes": handle.getsampwidth(),
            "frames": handle.getnframes(),
            "duration_seconds": handle.getnframes() / handle.getframerate(),
        }


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def write_audio(path: Path, audio: np.ndarray, sample_rate: int, speed: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".qwen-tts-", dir=path.parent) as temp_value:
        temp = Path(temp_value)
        native = temp / "native.wav"
        final = temp / "final.wav"
        audio_write(native, audio, sample_rate, format="wav")
        if abs(speed - 1.0) < 1e-9:
            os.replace(native, path)
            return
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required when Qwen --speed is not 1.0")
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(native),
                "-filter:a",
                f"atempo={speed:.8f}",
                "-ar",
                str(sample_rate),
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(final),
            ],
            check=True,
        )
        os.replace(final, path)


def cached(
    sidecar: Path,
    output: Path,
    expected_fingerprint: str,
    expected_model_validation: dict,
) -> dict | None:
    if not sidecar.is_file() or not output.is_file():
        return None
    try:
        value = read_json(sidecar)
        if value.get("fingerprint") != expected_fingerprint:
            return None
        if not model_validation_cache_matches(
            value.get("model_validation"), expected_model_validation
        ):
            return None
        if value.get("output_sha256") != sha256_file(output):
            return None
        return value
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()

    request = read_json(args.request)
    config = read_json(CONFIG_PATH)
    registry = read_json(REGISTRY_PATH)
    selection = request["selection"]
    voice_id = selection["resolved_voice_id"]
    voice = next((item for item in registry["voices"] if item["id"] == voice_id), None)
    if voice is None or selection["engine"] != config["qwen_base"]["engine"]:
        raise SystemExit(f"Qwen worker received invalid voice selection: {voice_id}")

    reference = (REGISTRY_PATH.parent / voice["reference_audio"]).resolve()
    if not reference.is_file():
        raise SystemExit(f"missing reference audio for {voice_id}: {reference}")
    actual_reference_sha = sha256_file(reference)
    if actual_reference_sha != voice["reference_sha256"]:
        raise SystemExit(
            f"reference SHA mismatch for {voice_id}: "
            f"expected {voice['reference_sha256']}, got {actual_reference_sha}"
        )

    qwen = config["qwen_base"]
    generation = qwen["generation"]
    actual_mlx_audio_version = installed_mlx_audio_version()
    model_path, model_validation = resolve_verified_model(
        config, actual_mlx_audio_version
    )
    pending: list[tuple[dict, str, Path, Path, dict]] = []
    for item in request["items"]:
        output = Path(item["output"]).resolve()
        sidecar = output.with_suffix(output.suffix + ".tts.json")
        speed = float(item.get("speed", 1.0))
        language = item.get("language") or qwen["language"]
        fp_inputs = fingerprint_inputs(
            qwen=qwen,
            selection=selection,
            voice_id=voice_id,
            reference_sha256=actual_reference_sha,
            reference_text=registry["reference_text"],
            item=item,
            language=language,
            speed=speed,
        )
        fp = fingerprint(fp_inputs)
        hit = (
            None
            if request.get("force")
            else cached(sidecar, output, fp, model_validation)
        )
        if hit is not None:
            print(f"reuse {output}  voice={voice_id} dur={hit['wav']['duration_seconds']:.2f}s")
        else:
            pending.append((item, fp, output, sidecar, fp_inputs))

    if not pending:
        return 0

    started = time.perf_counter()
    model = load_model(model_path)
    model_load_seconds = time.perf_counter() - started
    # Revalidate after model loading closes the cheap receipt/stat TOCTOU window:
    # generation only starts if the exact validated tree remained unchanged.
    try:
        post_load_validation = validate_receipt(
            model_root=model_path,
            manifest_file=manifest_path(config, TTS_ROOT),
            qwen=qwen,
            mlx_audio_version=actual_mlx_audio_version,
            tts_root=TTS_ROOT,
        )
    except (OSError, ProvenanceError) as exc:
        raise SystemExit(
            f"Qwen model provenance changed while loading; refusing generation: {exc}"
        ) from exc
    if post_load_validation != model_validation:
        raise SystemExit("Qwen model validation changed while loading; refusing generation")
    print(f"loaded {qwen['model_id']} in {model_load_seconds:.2f}s")

    for item, fp, output, sidecar, fp_inputs in pending:
        speed = float(item.get("speed", 1.0))
        language = item.get("language") or qwen["language"]
        seed = derived_seed(int(generation["seed"]), voice_id, item["text"], language)
        set_seed(seed)
        started = time.perf_counter()
        results = list(
            model.generate(
                text=item["text"],
                ref_audio=str(reference),
                ref_text=registry["reference_text"],
                lang_code=language,
                temperature=float(generation["temperature"]),
                top_k=int(generation["top_k"]),
                top_p=float(generation["top_p"]),
                repetition_penalty=float(generation["repetition_penalty"]),
                max_tokens=int(generation["max_tokens"]),
                verbose=False,
                stream=False,
            )
        )
        elapsed = time.perf_counter() - started
        audio, sample_rate, metrics = flatten_audio(results)
        audio = trim_edges(
            audio,
            sample_rate,
            float(generation["trim_threshold_dbfs"]),
            int(generation["trim_padding_ms"]),
        )
        write_audio(output, audio, sample_rate, speed)
        info = wav_info(output)
        if info["channels"] != 1 or info["sample_rate_hz"] != qwen["sample_rate_hz"]:
            raise RuntimeError(f"unexpected output format: {info}")
        normalized = "source_text" in item
        metadata = {
            "schema_version": "1.1.0" if normalized else "1.0.0",
            "item_id": item.get("id"),
            "text": item["text"],
            "text_sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
            "selection": selection,
            "resolved_voice_id": voice_id,
            "engine": qwen["engine"],
            "model_id": qwen["model_id"],
            "model_revision": qwen["model_revision"],
            "model_tree_sha256": qwen["model_tree_sha256"],
            "model_validation": model_validation,
            "reference_audio": str(reference.relative_to(TTS_ROOT)),
            "reference_sha256": actual_reference_sha,
            "language": language,
            "speed": speed,
            "seed": seed,
            "generation_seconds": elapsed,
            "model_load_seconds": model_load_seconds,
            "model_metrics": metrics,
            "fingerprint": fp,
            "fingerprint_inputs": fp_inputs,
            "output": os.path.relpath(output, start=sidecar.parent),
            "output_sha256": sha256_file(output),
            "wav": info,
        }
        if normalized:
            metadata.update(
                {
                    "source_text": item["source_text"],
                    "normalized_text": item["text"],
                    "text_normalization": item["text_normalization"],
                }
            )
        atomic_json(sidecar, metadata)
        print(f"wrote {output}  voice={voice_id} speed={speed} dur={info['duration_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
