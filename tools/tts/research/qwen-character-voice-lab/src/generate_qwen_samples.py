#!/usr/bin/env python3
"""Generate original character voice masters, then clone them for reusable samples.

This experiment is deliberately offline-only. It requires an Apple Silicon process
with Metal access and local Qwen3-TTS MLX model directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import wave
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parents[3]
DEFAULT_MANIFEST = EXPERIMENT_ROOT / "manifest.json"


def bootstrap_offline_runtime() -> None:
    runtime_root = EXPERIMENT_ROOT / "work" / "runtime"
    paths = {
        "HF_HOME": runtime_root / "hf",
        "HF_HUB_CACHE": runtime_root / "hf" / "hub",
        "HUGGINGFACE_HUB_CACHE": runtime_root / "hf" / "hub",
        "HF_XET_CACHE": runtime_root / "hf" / "xet",
        "TRANSFORMERS_CACHE": runtime_root / "transformers",
        "XDG_CACHE_HOME": runtime_root / "xdg-cache",
        "XDG_CONFIG_HOME": runtime_root / "xdg-config",
        "XDG_DATA_HOME": runtime_root / "xdg-data",
        "PIP_CACHE_DIR": runtime_root / "pip-cache",
        "TMPDIR": runtime_root / "tmp",
        "TMP": runtime_root / "tmp",
        "TEMP": runtime_root / "tmp",
        "PYTHONPYCACHEPREFIX": runtime_root / "python-cache",
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


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_fingerprint(value: dict) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cached_record(
    raw_path: Path, ready_path: Path, meta_path: Path, fingerprint: str
) -> dict | None:
    if not raw_path.is_file() or not ready_path.is_file() or not meta_path.is_file():
        return None
    try:
        value = load_json(meta_path)
        if value.get("fingerprint") != fingerprint:
            return None
        if value.get("raw_sha256") != sha256(raw_path):
            return None
        if value.get("ready_sha256") != sha256(ready_path):
            return None
        return value
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def derived_seed(base: int, *parts: str) -> int:
    payload = ":".join([str(base), *parts]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    mx.random.seed(seed)


def resolve_model(config: dict, env_name: str) -> Path:
    override = os.environ.get(env_name)
    value = override or config["default_path"]
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    if not candidate.is_dir():
        raise SystemExit(f"missing local model directory: {candidate}")
    if not (candidate / "config.json").is_file():
        raise SystemExit(f"invalid model directory (config.json missing): {candidate}")
    return candidate


def flatten_audio(results: list) -> tuple[np.ndarray, int, list[dict]]:
    if not results:
        raise RuntimeError("model returned no audio")
    sample_rates = {int(item.sample_rate) for item in results}
    if len(sample_rates) != 1:
        raise RuntimeError(f"mixed sample rates: {sorted(sample_rates)}")
    arrays = [np.asarray(item.audio, dtype=np.float32).reshape(-1) for item in results]
    audio = arrays[0] if len(arrays) == 1 else np.concatenate(arrays)
    metrics = []
    for item in results:
        metrics.append(
            {
                "reported_audio_duration": str(getattr(item, "audio_duration", "")),
                "processing_seconds": getattr(item, "processing_time_seconds", None),
                "peak_memory_gb": getattr(item, "peak_memory_usage", None),
                "token_count": getattr(item, "token_count", None),
            }
        )
    return audio, sample_rates.pop(), metrics


def trim_edges(
    audio: np.ndarray, sample_rate: int, threshold_dbfs: float, padding_ms: int
) -> tuple[np.ndarray, dict]:
    mono = audio if audio.ndim == 1 else audio.mean(axis=1)
    frame_size = max(1, int(sample_rate * 0.02))
    frame_count = (len(mono) + frame_size - 1) // frame_size
    padded = np.pad(mono, (0, frame_count * frame_size - len(mono)))
    rms = np.sqrt(np.mean(padded.reshape(frame_count, frame_size) ** 2, axis=1))
    threshold = 10 ** (threshold_dbfs / 20.0)
    active = np.flatnonzero(rms >= threshold)
    if not len(active):
        raise RuntimeError("generated audio contains no samples above trim threshold")
    pad_samples = int(sample_rate * padding_ms / 1000)
    start = max(0, int(active[0] * frame_size) - pad_samples)
    end = min(len(audio), int((active[-1] + 1) * frame_size) + pad_samples)
    return audio[start:end], {
        "start_trim_seconds": start / sample_rate,
        "end_trim_seconds": (len(audio) - end) / sample_rate,
        "threshold_dbfs": threshold_dbfs,
        "padding_ms": padding_ms,
    }


def write_pair(
    raw_path: Path,
    ready_path: Path,
    audio: np.ndarray,
    sample_rate: int,
    generation: dict,
) -> dict:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    ready_path.parent.mkdir(parents=True, exist_ok=True)
    audio_write(raw_path, audio, sample_rate, format="wav")
    trimmed, trim = trim_edges(
        audio,
        sample_rate,
        float(generation["trim_threshold_dbfs"]),
        int(generation["trim_padding_ms"]),
    )
    audio_write(ready_path, trimmed, sample_rate, format="wav")
    return {
        "raw": str(raw_path.relative_to(EXPERIMENT_ROOT)),
        "raw_sha256": sha256(raw_path),
        "raw_duration_seconds": len(audio) / sample_rate,
        "ready": str(ready_path.relative_to(EXPERIMENT_ROOT)),
        "ready_sha256": sha256(ready_path),
        "ready_duration_seconds": len(trimmed) / sample_rate,
        "sample_rate_hz": sample_rate,
        "trim": trim,
    }


def generate(
    model,
    *,
    text: str,
    language: str,
    generation: dict,
    seed: int,
    instruct: str | None = None,
    ref_audio: Path | None = None,
    ref_text: str | None = None,
) -> tuple[np.ndarray, int, dict]:
    set_seed(seed)
    kwargs = {
        "text": text,
        "lang_code": language,
        "temperature": float(generation["temperature"]),
        "top_k": int(generation["top_k"]),
        "top_p": float(generation["top_p"]),
        "repetition_penalty": float(generation["repetition_penalty"]),
        "max_tokens": int(generation["max_tokens"]),
        "verbose": False,
        "stream": False,
    }
    if instruct is not None:
        kwargs["instruct"] = instruct
    if ref_audio is not None:
        kwargs["ref_audio"] = str(ref_audio)
        kwargs["ref_text"] = ref_text
    started = time.perf_counter()
    results = list(model.generate(**kwargs))
    elapsed = time.perf_counter() - started
    audio, sample_rate, metrics = flatten_audio(results)
    return audio, sample_rate, {
        "seed": seed,
        "generation_seconds": elapsed,
        "model_metrics": metrics,
    }


def wav_info(path: Path) -> dict:
    with wave.open(str(path), "rb") as handle:
        return {
            "channels": handle.getnchannels(),
            "sample_rate_hz": handle.getframerate(),
            "sample_width_bytes": handle.getsampwidth(),
            "frames": handle.getnframes(),
            "duration_seconds": handle.getnframes() / handle.getframerate(),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--only", nargs="*", help="optional persona ids")
    parser.add_argument("--force", action="store_true", help="overwrite existing samples")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_json(manifest_path)
    personas = manifest["personas"]
    if args.only:
        wanted = set(args.only)
        personas = [item for item in personas if item["id"] in wanted]
        missing = wanted - {item["id"] for item in personas}
        if missing:
            raise SystemExit(f"unknown persona ids: {', '.join(sorted(missing))}")

    generation = manifest["generation"]
    texts = manifest["texts"]
    base_seed = int(generation["seed"])
    design_model_path = resolve_model(
        manifest["models"]["voice_design"], "QWEN_VOICE_DESIGN_MODEL"
    )
    base_model_path = resolve_model(manifest["models"]["base_clone"], "QWEN_BASE_MODEL")

    output_root = EXPERIMENT_ROOT / "outputs" / "qwen3-tts"
    qa_path = EXPERIMENT_ROOT / "qa" / "qwen-generation-report.json"
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0.0",
        "manifest": str(manifest_path.relative_to(REPO_ROOT)),
        "offline": True,
        "runtime": {
            "python": sys.version.split()[0],
            "mlx_audio": manifest["runtime"]["version"],
        },
        "models": {
            "voice_design": {
                "id": manifest["models"]["voice_design"]["id"],
                "revision": manifest["models"]["voice_design"]["revision"],
                "path": str(design_model_path),
            },
            "base_clone": {
                "id": manifest["models"]["base_clone"]["id"],
                "revision": manifest["models"]["base_clone"]["revision"],
                "path": str(base_model_path),
            },
        },
        "personas": [],
    }

    pending_master = []
    for persona in personas:
        root = output_root / persona["id"]
        raw = root / "raw" / "voice-master.wav"
        ready = root / "ready" / "voice-master.wav"
        meta_path = root / "master-meta.json"
        seed = derived_seed(base_seed, persona["id"], "master")
        fingerprint = json_fingerprint(
            {
                "stage": "voice-design-master",
                "model_id": manifest["models"]["voice_design"]["id"],
                "model_revision": manifest["models"]["voice_design"]["revision"],
                "persona": persona,
                "text": texts["voice_master"],
                "language": "Chinese",
                "generation": generation,
                "seed": seed,
            }
        )
        if args.force or cached_record(raw, ready, meta_path, fingerprint) is None:
            pending_master.append(persona)

    if pending_master:
        print(f"loading VoiceDesign model: {design_model_path.name}")
        started = time.perf_counter()
        design_model = load_model(design_model_path)
        print(f"VoiceDesign loaded in {time.perf_counter() - started:.2f}s")
        for index, persona in enumerate(personas, 1):
            root = output_root / persona["id"]
            raw = root / "raw" / "voice-master.wav"
            ready = root / "ready" / "voice-master.wav"
            meta_path = root / "master-meta.json"
            seed = derived_seed(base_seed, persona["id"], "master")
            fingerprint_payload = {
                "stage": "voice-design-master",
                "model_id": manifest["models"]["voice_design"]["id"],
                "model_revision": manifest["models"]["voice_design"]["revision"],
                "persona": persona,
                "text": texts["voice_master"],
                "language": "Chinese",
                "generation": generation,
                "seed": seed,
            }
            fingerprint = json_fingerprint(fingerprint_payload)
            cached = None if args.force else cached_record(raw, ready, meta_path, fingerprint)
            if cached is not None:
                print(f"[{index}/{len(personas)}] reuse master {persona['id']}")
                continue
            print(f"[{index}/{len(personas)}] design {persona['id']} / {persona['label']}")
            audio, sample_rate, meta = generate(
                design_model,
                text=texts["voice_master"],
                language="Chinese",
                instruct=persona["description"],
                generation=generation,
                seed=seed,
            )
            meta.update(write_pair(raw, ready, audio, sample_rate, generation))
            meta.update(
                {
                    "stage": "voice-design-master",
                    "persona_id": persona["id"],
                    "persona_label": persona["label"],
                    "text": texts["voice_master"],
                    "language": "Chinese",
                    "fingerprint": fingerprint,
                    "fingerprint_inputs": fingerprint_payload,
                }
            )
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        del design_model
        mx.clear_cache()

    print(f"loading Base clone model: {base_model_path.name}")
    started = time.perf_counter()
    base_model = load_model(base_model_path)
    base_load_seconds = time.perf_counter() - started
    print(f"Base loaded in {base_load_seconds:.2f}s")

    for index, persona in enumerate(personas, 1):
        root = output_root / persona["id"]
        master_raw = root / "raw" / "voice-master.wav"
        if not master_raw.is_file():
            raise RuntimeError(f"missing voice master: {master_raw}")
        persona_report = {
            "id": persona["id"],
            "label": persona["label"],
            "group": persona["group"],
            "description": persona["description"],
            "master": {
                "path": str(master_raw.relative_to(EXPERIMENT_ROOT)),
                "sha256": sha256(master_raw),
                "wav": wav_info(master_raw),
                "metadata": load_json(root / "master-meta.json"),
            },
            "samples": [],
        }
        for text_id, language in (("showcase", "Chinese"), ("mixed_language", "Auto")):
            raw = root / "raw" / f"{text_id}.wav"
            ready = root / "ready" / f"{text_id}.wav"
            meta_path = root / f"{text_id}-meta.json"
            seed = derived_seed(base_seed, persona["id"], text_id)
            fingerprint_payload = {
                "stage": "base-clone",
                "model_id": manifest["models"]["base_clone"]["id"],
                "model_revision": manifest["models"]["base_clone"]["revision"],
                "persona_id": persona["id"],
                "text_id": text_id,
                "text": texts[text_id],
                "language": language,
                "reference_audio_sha256": sha256(master_raw),
                "reference_text": texts["voice_master"],
                "generation": generation,
                "seed": seed,
            }
            fingerprint = json_fingerprint(fingerprint_payload)
            cached = None if args.force else cached_record(raw, ready, meta_path, fingerprint)
            if cached is not None:
                print(f"[{index}/{len(personas)}] reuse {persona['id']} {text_id}")
                sample_meta = dict(cached)
                sample_meta["cache_hit"] = True
            else:
                print(f"[{index}/{len(personas)}] clone {persona['id']} {text_id}")
                audio, sample_rate, sample_meta = generate(
                    base_model,
                    text=texts[text_id],
                    language=language,
                    ref_audio=master_raw,
                    ref_text=texts["voice_master"],
                    generation=generation,
                    seed=seed,
                )
                sample_meta.update(write_pair(raw, ready, audio, sample_rate, generation))
                sample_meta.update(
                    {
                        "text_id": text_id,
                        "text": texts[text_id],
                        "language": language,
                        "cache_hit": False,
                        "stage": "base-clone",
                        "persona_id": persona["id"],
                        "fingerprint": fingerprint,
                        "fingerprint_inputs": fingerprint_payload,
                    }
                )
                meta_path.write_text(
                    json.dumps(sample_meta, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            persona_report["samples"].append(sample_meta)
        report["personas"].append(persona_report)

    report["models"]["base_clone"]["load_seconds"] = base_load_seconds
    qa_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {qa_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
