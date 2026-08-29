#!/usr/bin/env python3
"""Resolve one project-level voice choice from a selector or original task brief."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from voice_registry import VoiceRegistry, resolve_selector, resolve_task_prompt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--voice", help="exact registered ID, name, slug or alias")
    source.add_argument("--task-prompt", help="literal original task brief")
    source.add_argument("--task-prompt-file", type=Path, help="UTF-8 task brief file")
    parser.add_argument(
        "--model-choice",
        help="model-selected exact ID/name/alias from the standard decision pool",
    )
    parser.add_argument(
        "--model-reason",
        help="one concise reason based on project emotion and narrative expression",
    )
    parser.add_argument(
        "--model-confidence",
        choices=("high", "medium", "low"),
        help="high/medium selects the model choice; low triggers random fallback",
    )
    parser.add_argument("-o", "--output", type=Path, help="write selection JSON")
    parser.add_argument("--list", action="store_true", help="list registered voices")
    args = parser.parse_args()

    model_values = (args.model_choice, args.model_reason, args.model_confidence)
    if any(value is not None for value in model_values):
        if args.voice is not None or args.list:
            parser.error("model decision fields are only valid with a task prompt")
        if args.model_reason is None or args.model_confidence is None:
            parser.error("model decisions require --model-reason and --model-confidence")
        if args.model_confidence in {"high", "medium"} and args.model_choice is None:
            parser.error("high/medium model confidence requires --model-choice")

    registry = VoiceRegistry.load()
    if args.list:
        value = {
            "preflight_voice_id": registry.preflight_id,
            "decision_voice_pool": registry.decision_pool_ids,
            "random_voice_pool": registry.random_pool_ids,
            "voices": [
                {
                    "id": voice["id"],
                    "name": voice["name"],
                    "slug": voice["slug"],
                    "aliases": voice.get("aliases", []),
                    "decision_profile": voice.get("decision_profile"),
                    "in_decision_pool": voice["id"] in registry.decision_pool_ids,
                }
                for voice in registry.voices
            ],
            "legacy_kokoro": registry.config["legacy_kokoro"]["voices"],
        }
    elif args.voice is not None:
        value = resolve_selector(registry, args.voice)
    else:
        if args.task_prompt_file:
            prompt = args.task_prompt_file.read_text(encoding="utf-8")
        else:
            prompt = args.task_prompt or ""
        value = resolve_task_prompt(
            registry,
            prompt,
            model_choice=args.model_choice,
            model_reason=args.model_reason,
            model_confidence=args.model_confidence,
        )

    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(args.output)
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
