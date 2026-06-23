#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tools_python="../../tools/tts/venv/bin/python"
"$tools_python" build/make_clips.py

