#!/usr/bin/env python3
"""Generate isolated Qwen VoiceDesign masters and one common Base-clone sample.

The script is offline-only and refuses to import MLX until the repository's
stdlib-only Metal preflight has passed in the current process context.
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


LAB_ROOT = Path(__file__).resolve().parents[1]
TTS_ROOT = LAB_ROOT.parents[1]
REPO_ROOT = LAB_ROOT.parents[3]
MANIFEST_PATH = LAB_ROOT / "manifest.json"
OUTPUT_ROOT = LAB_ROOT / "outputs"

sys.path.insert(0, str(TTS_ROOT))
from metal_preflight import MetalUnavailable, require_default_metal_device  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(value: dict) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def derived_seed(base: int, *parts: str) -> int:
    payload = ":".join([str(base), *parts]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def bootstrap_offline_runtime() -> None:
    runtime_root = OUTPUT_ROOT / "runtime"
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


def resolve_model(config: dict) -> Path:
    override = os.environ.get(config["path_env"])
    candidate = Path(override or config["default_path"])
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    if not candidate.is_dir() or not (candidate / "config.json").is_file():
        raise SystemExit(f"missing or invalid local model: {candidate}")
    return candidate


def trim_edges(audio, np, sample_rate: int, threshold_dbfs: float, padding_ms: int):
    mono = audio if audio.ndim == 1 else audio.mean(axis=1)
    frame_size = max(1, int(sample_rate * 0.02))
    frame_count = (len(mono) + frame_size - 1) // frame_size
    padded = np.pad(mono, (0, frame_count * frame_size - len(mono)))
    rms = np.sqrt(np.mean(padded.reshape(frame_count, frame_size) ** 2, axis=1))
    active = np.flatnonzero(rms >= 10 ** (threshold_dbfs / 20.0))
    if not len(active):
        raise RuntimeError("generated audio contains no active samples")
    pad_samples = int(sample_rate * padding_ms / 1000)
    start = max(0, int(active[0] * frame_size) - pad_samples)
    end = min(len(audio), int((active[-1] + 1) * frame_size) + pad_samples)
    return audio[start:end]


def flatten_results(results: list, np):
    if not results:
        raise RuntimeError("model returned no audio")
    sample_rates = {int(item.sample_rate) for item in results}
    if len(sample_rates) != 1:
        raise RuntimeError(f"model returned mixed sample rates: {sorted(sample_rates)}")
    arrays = [np.asarray(item.audio, dtype=np.float32).reshape(-1) for item in results]
    audio = arrays[0] if len(arrays) == 1 else np.concatenate(arrays)
    metrics = [
        {
            "reported_audio_duration": str(getattr(item, "audio_duration", "")),
            "processing_seconds": getattr(item, "processing_time_seconds", None),
            "peak_memory_gb": getattr(item, "peak_memory_usage", None),
            "token_count": getattr(item, "token_count", None),
        }
        for item in results
    ]
    return audio, sample_rates.pop(), metrics


def generate_audio(
    model,
    *,
    mx,
    np,
    text: str,
    language: str,
    generation: dict,
    seed: int,
    instruct: str | None = None,
    ref_audio: Path | None = None,
    ref_text: str | None = None,
):
    random.seed(seed)
    np.random.seed(seed)
    mx.random.seed(seed)
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
    audio, sample_rate, metrics = flatten_results(list(model.generate(**kwargs)), np)
    return audio, sample_rate, {
        "seed": seed,
        "generation_seconds": time.perf_counter() - started,
        "model_metrics": metrics,
    }


def write_audio_pair(audio_write, np, audio, sample_rate: int, root: Path, name: str, generation: dict):
    raw_path = root / "raw" / f"{name}.wav"
    ready_path = root / "ready" / f"{name}.wav"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    ready_path.parent.mkdir(parents=True, exist_ok=True)
    audio_write(raw_path, audio, sample_rate, format="wav")
    ready = trim_edges(
        audio,
        np,
        sample_rate,
        float(generation["trim_threshold_dbfs"]),
        int(generation["trim_padding_ms"]),
    )
    audio_write(ready_path, ready, sample_rate, format="wav")
    return {
        "raw": str(raw_path.relative_to(LAB_ROOT)),
        "raw_sha256": sha256(raw_path),
        "raw_duration_seconds": len(audio) / sample_rate,
        "ready": str(ready_path.relative_to(LAB_ROOT)),
        "ready_sha256": sha256(ready_path),
        "ready_duration_seconds": len(ready) / sample_rate,
        "sample_rate_hz": sample_rate,
    }


def wav_valid(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as handle:
            return (
                handle.getnchannels() == 1
                and handle.getframerate() == 24000
                and handle.getnframes() > 24000
            )
    except (OSError, EOFError, wave.Error):
        return False


def cache_hit(meta_path: Path, expected: str, required: list[Path]) -> dict | None:
    if not meta_path.is_file() or not all(wav_valid(path) for path in required):
        return None
    try:
        value = read_json(meta_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if value.get("fingerprint") != expected:
        return None
    hashes = value.get("output_hashes", {})
    for path in required:
        if hashes.get(path.name + ":" + path.parent.name) != sha256(path):
            return None
    return value


def output_hashes(paths: list[Path]) -> dict:
    return {path.name + ":" + path.parent.name: sha256(path) for path in paths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", help="optional persona IDs")
    parser.add_argument(
        "--sample",
        choices=("showcase", "mixed_language", "all"),
        default="showcase",
        help="Base-clone sample set to generate",
    )
    parser.add_argument("--force", action="store_true", help="regenerate selected files")
    parser.add_argument("--list", action="store_true", help="list persona IDs without loading MLX")
    args = parser.parse_args()

    manifest = read_json(MANIFEST_PATH)
    personas = manifest["personas"]
    if args.only:
        wanted = set(args.only)
        personas = [persona for persona in personas if persona["id"] in wanted]
        missing = wanted - {persona["id"] for persona in personas}
        if missing:
            raise SystemExit("unknown persona IDs: " + ", ".join(sorted(missing)))
    if args.list:
        for persona in personas:
            print(f"{persona['id']}\t{persona['label']}\t{persona['category']}")
        return 0

    try:
        require_default_metal_device()
    except MetalUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 78
    print("QWEN METAL PREFLIGHT: PASS", flush=True)
    bootstrap_offline_runtime()

    import mlx.core as mx
    import numpy as np
    from mlx_audio.audio_io import write as audio_write
    from mlx_audio.tts.utils import load_model

    generation = manifest["generation"]
    texts = manifest["texts"]
    base_seed = int(generation["seed"])
    design_config = manifest["models"]["voice_design"]
    base_config = manifest["models"]["base_clone"]
    design_path = resolve_model(design_config)
    base_path = resolve_model(base_config)
    voice_root = OUTPUT_ROOT / "voices"

    pending_masters = []
    master_records: dict[str, dict] = {}
    for persona in personas:
        root = voice_root / persona["id"]
        raw = root / "raw" / "voice-master.wav"
        ready = root / "ready" / "voice-master.wav"
        meta_path = root / "master-meta.json"
        seed = derived_seed(base_seed, persona["id"], "master")
        inputs = {
            "stage": "voice-design-master",
            "model_id": design_config["id"],
            "model_revision": design_config["revision"],
            "persona": persona,
            "text": texts["voice_master"],
            "language": "Chinese",
            "generation": generation,
            "seed": seed,
        }
        expected = fingerprint(inputs)
        cached = None if args.force else cache_hit(meta_path, expected, [raw, ready])
        if cached is None:
            pending_masters.append((persona, inputs, expected))
        else:
            master_records[persona["id"]] = cached

    if pending_masters:
        print(f"loading VoiceDesign model: {design_path.name}", flush=True)
        started = time.perf_counter()
        design_model = load_model(design_path)
        print(f"VoiceDesign loaded in {time.perf_counter() - started:.2f}s", flush=True)
        for index, (persona, inputs, expected) in enumerate(pending_masters, 1):
            print(
                f"MASTER {index:02d}/{len(pending_masters):02d} {persona['id']} / {persona['label']}",
                flush=True,
            )
            audio, sample_rate, record = generate_audio(
                design_model,
                mx=mx,
                np=np,
                text=texts["voice_master"],
                language="Chinese",
                instruct=persona["description"],
                generation=generation,
                seed=inputs["seed"],
            )
            root = voice_root / persona["id"]
            record.update(
                write_audio_pair(
                    audio_write, np, audio, sample_rate, root, "voice-master", generation
                )
            )
            paths = [root / "raw" / "voice-master.wav", root / "ready" / "voice-master.wav"]
            record.update(
                {
                    "persona_id": persona["id"],
                    "persona_label": persona["label"],
                    "fingerprint": expected,
                    "fingerprint_inputs": inputs,
                    "output_hashes": output_hashes(paths),
                }
            )
            write_json(root / "master-meta.json", record)
            master_records[persona["id"]] = record
        del design_model
        mx.clear_cache()

    sample_specs = {
        "showcase": ("Chinese", "showcase"),
        "mixed_language": ("Auto", "mixed-language"),
    }
    selected_sample_ids = (
        list(sample_specs) if args.sample == "all" else [args.sample]
    )
    pending_samples = []
    sample_records: dict[str, dict] = {}
    for persona in personas:
        root = voice_root / persona["id"]
        reference = root / "raw" / "voice-master.wav"
        if not wav_valid(reference):
            raise RuntimeError(f"missing valid reference master: {reference}")
        for sample_id in selected_sample_ids:
            language, filename = sample_specs[sample_id]
            raw = root / "raw" / f"{filename}.wav"
            ready = root / "ready" / f"{filename}.wav"
            meta_path = root / f"{filename}-meta.json"
            seed = derived_seed(base_seed, persona["id"], sample_id)
            inputs = {
                "stage": f"base-clone-{sample_id}",
                "model_id": base_config["id"],
                "model_revision": base_config["revision"],
                "persona_id": persona["id"],
                "sample_id": sample_id,
                "text": texts[sample_id],
                "language": language,
                "reference_audio_sha256": sha256(reference),
                "reference_text": texts["voice_master"],
                "generation": generation,
                "seed": seed,
            }
            expected = fingerprint(inputs)
            cached = None if args.force else cache_hit(meta_path, expected, [raw, ready])
            key = f"{persona['id']}:{sample_id}"
            if cached is None:
                pending_samples.append((persona, sample_id, filename, inputs, expected))
            else:
                sample_records[key] = cached

    if pending_samples:
        print(f"loading Base model: {base_path.name}", flush=True)
        started = time.perf_counter()
        base_model = load_model(base_path)
        print(f"Base loaded in {time.perf_counter() - started:.2f}s", flush=True)
        for index, (persona, sample_id, filename, inputs, expected) in enumerate(
            pending_samples, 1
        ):
            print(
                f"SAMPLE {index:02d}/{len(pending_samples):02d} "
                f"{persona['id']} {sample_id} / {persona['label']}",
                flush=True,
            )
            root = voice_root / persona["id"]
            audio, sample_rate, record = generate_audio(
                base_model,
                mx=mx,
                np=np,
                text=texts[sample_id],
                language=inputs["language"],
                ref_audio=root / "raw" / "voice-master.wav",
                ref_text=texts["voice_master"],
                generation=generation,
                seed=inputs["seed"],
            )
            record.update(
                write_audio_pair(
                    audio_write, np, audio, sample_rate, root, filename, generation
                )
            )
            paths = [root / "raw" / f"{filename}.wav", root / "ready" / f"{filename}.wav"]
            record.update(
                {
                    "persona_id": persona["id"],
                    "persona_label": persona["label"],
                    "fingerprint": expected,
                    "fingerprint_inputs": inputs,
                    "output_hashes": output_hashes(paths),
                }
            )
            write_json(root / f"{filename}-meta.json", record)
            sample_records[f"{persona['id']}:{sample_id}"] = record
        del base_model
        mx.clear_cache()

    report = {
        "schema_version": "1.0.0",
        "experiment_id": manifest["experiment_id"],
        "generated_persona_count": len(personas),
        "requested_persona_ids": [persona["id"] for persona in personas],
        "models": {
            "voice_design": {"id": design_config["id"], "revision": design_config["revision"]},
            "base_clone": {"id": base_config["id"], "revision": base_config["revision"]},
        },
        "masters": [master_records[persona["id"]] for persona in personas],
        "sample_ids": selected_sample_ids,
        "samples": [
            sample_records[f"{persona['id']}:{sample_id}"]
            for persona in personas
            for sample_id in selected_sample_ids
        ],
    }
    write_json(OUTPUT_ROOT / "qa" / "generation-report.json", report)
    print(f"GENERATION PASS: voices={len(personas)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
