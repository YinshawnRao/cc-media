#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
../../tools/tts/venv/bin/python build/make_clips.py
