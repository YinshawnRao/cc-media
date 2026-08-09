#!/usr/bin/env python3
"""Unified cc-media TTS dispatcher; new tasks default to CV002 治愈少女."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from voice_registry import (
    VoiceRegistry,
    default_selection,
    resolve_selector,
    resolve_task_prompt,
)


TTS_ROOT = Path(__file__).resolve().parent


def read_input(value: str, base: Path | None = None) -> str:
    candidate = Path(value)
    if base is not None and not candidate.is_absolute():
        candidate = base / candidate
    try:
        is_file = candidate.is_file()
    except OSError:
        is_file = False
    return candidate.read_text(encoding="utf-8").strip() if is_file else value.strip()


def resolve_runtime(config: dict, engine: str) -> Path:
    runtime = config["runtime"]
    if engine == config["qwen_base"]["engine"]:
        env_name = runtime["qwen_python_env"]
        values = runtime["qwen_python_candidates"]
        label = "Qwen/MLX"
        required_modules = ("mlx", "mlx_audio")
    elif engine == config["legacy_kokoro"]["engine"]:
        env_name = runtime["kokoro_python_env"]
        values = runtime["kokoro_python_candidates"]
        label = "Kokoro"
        required_modules = ("kokoro", "soundfile")
    else:
        raise SystemExit(f"unsupported TTS engine: {engine}")

    candidates: list[Path] = []
    override = os.environ.get(env_name)
    if override:
        candidate = Path(override).expanduser()
        candidates.append(
            candidate if candidate.is_absolute() else Path(os.path.abspath(TTS_ROOT / candidate))
        )
    for value in values:
        candidate = Path(value)
        candidates.append(
            candidate if candidate.is_absolute() else Path(os.path.abspath(TTS_ROOT / candidate))
        )
    rejected: list[str] = []
    for candidate in candidates:
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            rejected.append(f"{candidate} (missing or not executable)")
            continue
        probe = (
            "import importlib.util,sys; "
            f"mods={required_modules!r}; "
            "missing=[m for m in mods if importlib.util.find_spec(m) is None]; "
            "sys.exit(1 if missing else 0)"
        )
        try:
            completed = subprocess.run(
                [str(candidate), "-c", probe], capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            rejected.append(f"{candidate} (probe failed: {exc})")
            continue
        if completed.returncode == 0:
            return candidate
        rejected.append(f"{candidate} (missing modules: {', '.join(required_modules)})")
    rendered = "\n  - ".join(rejected)
    raise SystemExit(
        f"{label} runtime is unavailable. Checked:\n  - {rendered}\n"
        f"Set {env_name} to the required Python interpreter."
    )


def load_selection_file(path: Path, registry: VoiceRegistry) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("registry_sha256") != registry.registry_sha256:
        raise SystemExit("selection file registry hash is stale; resolve the task brief again")
    if value.get("config_sha256") != registry.config_sha256:
        raise SystemExit("selection file config hash is stale; resolve the task brief again")
    voice_id = value.get("resolved_voice_id", "")
    if voice_id.startswith("kokoro:"):
        if registry.legacy_voice(voice_id) is None:
            raise SystemExit(f"selection file contains unknown legacy voice: {voice_id}")
    elif registry.by_id(voice_id) is None:
        raise SystemExit(f"selection file contains unknown voice: {voice_id}")
    return value


def write_selection(path: Path, selection: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def selection_for(args: argparse.Namespace, registry: VoiceRegistry, batch: dict | None) -> dict:
    if args.selection_file:
        return load_selection_file(args.selection_file.resolve(), registry)
    selector = args.voice if args.voice is not None else (batch or {}).get("voice")
    if selector is not None:
        return resolve_selector(registry, str(selector))
    if args.female:
        return resolve_selector(registry, "zf_xiaoyi")
    if args.task_prompt_file:
        prompt = args.task_prompt_file.read_text(encoding="utf-8")
        return resolve_task_prompt(registry, prompt)
    prompt = args.task_prompt
    if prompt is None and batch is not None:
        prompt = batch.get("task_prompt")
    if prompt is not None:
        return resolve_task_prompt(registry, prompt)
    return default_selection(registry, requested=None, reason="default_no_request")


def batch_items(path: Path, value: dict, default_speed: float, default_language: str) -> list[dict]:
    blocks = value.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise SystemExit("batch JSON must contain a non-empty blocks array")
    items = []
    for index, block in enumerate(blocks, 1):
        if not isinstance(block, dict):
            raise SystemExit(f"batch block {index} is not an object")
        if "text" in block:
            text = str(block["text"]).strip()
        elif "input" in block:
            text = read_input(str(block["input"]), path.parent)
        else:
            raise SystemExit(f"batch block {index} needs text or input")
        if not text:
            raise SystemExit(f"batch block {index} has empty text")
        if "output" not in block:
            raise SystemExit(f"batch block {index} needs output")
        output = Path(str(block["output"]))
        if not output.is_absolute():
            output = path.parent / output
        speed = float(block.get("speed", default_speed))
        if not 0.5 <= speed <= 2.0:
            raise SystemExit(f"batch block {index} speed must be between 0.5 and 2.0")
        items.append(
            {
                "id": block.get("id") or f"block-{index:03d}",
                "text": text,
                "output": str(output.resolve()),
                "language": block.get("language") or default_language,
                "speed": speed,
            }
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="literal text or UTF-8 text file")
    parser.add_argument("-o", "--output", type=Path, help="single WAV output")
    parser.add_argument("--batch", type=Path, help="batch JSON; loads the model once")
    parser.add_argument("--voice", help="exact CV ID/name/alias or legacy Kokoro ID")
    parser.add_argument(
        "--female",
        action="store_true",
        help="legacy compatibility only: Kokoro zf_xiaoyi; new tasks must omit it",
    )
    parser.add_argument("--task-prompt", help="original task brief used for voice resolution")
    parser.add_argument("--task-prompt-file", type=Path, help="UTF-8 original task brief")
    parser.add_argument("--selection-file", type=Path, help="reuse project voice-selection.json")
    parser.add_argument("--selection-output", type=Path, help="write resolved selection JSON")
    parser.add_argument("--resolve-only", action="store_true", help="resolve and stop")
    parser.add_argument("--list-voices", action="store_true")
    parser.add_argument("--language", default="Auto")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--force", action="store_true", help="ignore valid output cache")
    args = parser.parse_args()

    if not 0.5 <= args.speed <= 2.0:
        parser.error("--speed must be between 0.5 and 2.0")
    registry = VoiceRegistry.load()
    if args.list_voices:
        for voice in registry.voices:
            marker = " [DEFAULT]" if voice["id"] == registry.default_id else ""
            print(f"{voice['id']}  {voice['name']}  {voice['slug']}{marker}")
        print("legacy Kokoro (explicit only): " + " ".join(registry.config["legacy_kokoro"]["voices"]))
        return 0

    batch = None
    batch_path = None
    if args.batch:
        batch_path = args.batch.resolve()
        batch = json.loads(batch_path.read_text(encoding="utf-8"))
    if args.selection_file and any(
        [
            args.voice,
            args.female,
            args.task_prompt is not None,
            args.task_prompt_file,
            (batch or {}).get("voice"),
            (batch or {}).get("task_prompt"),
        ]
    ):
        parser.error(
            "--selection-file is the project source of truth and cannot be combined "
            "with another voice selector or task prompt"
        )
    selection = selection_for(args, registry, batch)
    if args.voice and args.female:
        print("warning: --voice overrides legacy --female", file=sys.stderr)
    if selection["fallback"]:
        print(
            f"warning: voice request could not be resolved uniquely; using "
            f"{selection['resolved_voice_id']} {selection['resolved_voice_name']} "
            f"({selection['resolution_reason']})",
            file=sys.stderr,
        )
    print(
        f"voice-selection {selection['resolved_voice_id']} "
        f"{selection['resolved_voice_name']} reason={selection['resolution_reason']}",
        file=sys.stderr,
    )
    if args.selection_output:
        write_selection(args.selection_output.resolve(), selection)
    if args.resolve_only:
        if not args.selection_output:
            print(json.dumps(selection, ensure_ascii=False, indent=2))
        return 0

    if batch is not None:
        assert batch_path is not None
        items = batch_items(batch_path, batch, args.speed, args.language)
    else:
        if args.input is None or args.output is None:
            parser.error("single generation requires input and --output, or use --batch")
        text = read_input(args.input)
        if not text:
            parser.error("input text is empty")
        items = [
            {
                "id": "single",
                "text": text,
                "output": str(args.output.resolve()),
                "language": args.language,
                "speed": args.speed,
            }
        ]

    engine = selection["engine"]
    python = resolve_runtime(registry.config, engine)
    worker = (
        TTS_ROOT / "engines" / "qwen_mlx.py"
        if engine == registry.config["qwen_base"]["engine"]
        else TTS_ROOT / "engines" / "kokoro_legacy.py"
    )
    request = {
        "schema_version": "1.0.0",
        "selection": selection,
        "items": items,
        "force": args.force,
    }
    with tempfile.TemporaryDirectory(prefix="cc-media-tts-") as temporary:
        request_path = Path(temporary) / "request.json"
        request_path.write_text(
            json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        completed = subprocess.run([str(python), str(worker), "--request", str(request_path)])
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
