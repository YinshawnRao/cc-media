#!/usr/bin/env python3
"""仅两段 TTS：开头 + 结尾。男声 zm_yunxi 偏慢节奏。"""
import json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parent.parent
out_dir = ROOT / "voice"
out_dir.mkdir(exist_ok=True)

BLOCKS = {
    "intro": {
        "text": "这不是一场真实演出，而是一次AI剪辑实验。我们试着让窦唯、王菲、窦靖童，在同一首歌里，完成一次跨时空接唱。",
        "speed": 0.95,
    },
    "outro": {
        "text": "这不是同一场演出，却像同一首歌，终于在时间里见了一面。",
        "speed": 0.92,
    },
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, cfg in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(cfg["text"], voice=VOICE, speed=cfg["speed"])]
    if not chunks:
        print(f"FAIL: {key}", file=sys.stderr); sys.exit(1)
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    fp = out_dir / f"{key}.wav"
    sf.write(fp, audio, SR)
    meta[key] = {"text": cfg["text"], "dur": round(len(audio) / SR, 3), "speed": cfg["speed"]}
    print(f"{key:8s} {meta[key]['dur']:6.2f}s")

(ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
print(f"TOTAL {round(sum(m['dur'] for m in meta.values()), 2)}s")
