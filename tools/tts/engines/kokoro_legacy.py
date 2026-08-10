#!/usr/bin/env python3
"""Legacy Kokoro worker retained for explicit historical voice IDs only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import wave
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline


TTS_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


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
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def cached(sidecar: Path, output: Path, expected_fingerprint: str) -> dict | None:
    if not sidecar.is_file() or not output.is_file():
        return None
    try:
        value = read_json(sidecar)
        if value.get("fingerprint") != expected_fingerprint:
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
    selection = request["selection"]
    voice_id = selection["resolved_voice_id"]
    if not voice_id.startswith("kokoro:"):
        raise SystemExit(f"Kokoro worker received invalid voice selection: {voice_id}")
    voice = voice_id.split(":", 1)[1]
    sample_rate = 24000

    records = []
    for item in request["items"]:
        output = Path(item["output"]).resolve()
        sidecar = output.with_suffix(output.suffix + ".tts.json")
        speed = float(item.get("speed", 1.0))
        fp_inputs = {
            "engine": "kokoro-misaki-zh",
            "model_id": "hexgrad/Kokoro-82M",
            "voice": voice,
            "selection": selection,
            "text": item["text"],
            "speed": speed,
        }
        fp = fingerprint(fp_inputs)
        hit = None if request.get("force") else cached(sidecar, output, fp)
        if hit is not None:
            print(f"reuse {output}  voice={voice} dur={hit['wav']['duration_seconds']:.2f}s")
        else:
            records.append((item, output, sidecar, speed, fp_inputs, fp))
    if not records:
        return 0

    pipeline = KPipeline(lang_code="z")
    for item, output, sidecar, speed, fp_inputs, fp in records:
        chunks = [audio for _, _, audio in pipeline(item["text"], voice=voice, speed=speed)]
        if not chunks:
            raise RuntimeError("Kokoro returned no audio")
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".kokoro-tts-", dir=output.parent) as temp:
            temporary = Path(temp) / "output.wav"
            sf.write(temporary, audio, sample_rate)
            os.replace(temporary, output)
        info = wav_info(output)
        metadata = {
            "schema_version": "1.0.0",
            "item_id": item.get("id"),
            "text": item["text"],
            "text_sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
            "selection": selection,
            "resolved_voice_id": voice_id,
            "engine": "kokoro-misaki-zh",
            "model_id": "hexgrad/Kokoro-82M",
            "speed": speed,
            "fingerprint": fp,
            "fingerprint_inputs": fp_inputs,
            "output": os.path.relpath(output, start=sidecar.parent),
            "output_sha256": sha256_file(output),
            "wav": info,
        }
        atomic_json(sidecar, metadata)
        print(f"wrote {output}  voice={voice} speed={speed} dur={info['duration_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
