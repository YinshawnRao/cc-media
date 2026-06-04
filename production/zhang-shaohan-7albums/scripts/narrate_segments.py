#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，张韶涵前7张专辑·冷门遗珠盘点。
读取 build/narration.txt（[key] / text 块），输出 audio/<key>.wav + narration.json。
预期 cwd = sandbox/zhang-shaohan-7albums。
"""
import json
import re
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

src = Path("build/narration.txt").read_text(encoding="utf-8")
BLOCKS = {}
cur = None
buf = []
for raw in src.splitlines():
    line = raw.rstrip()
    if not line or line.startswith("#"):
        continue
    m = re.match(r"^\[([a-z0-9_]+)\]\s*$", line)
    if m:
        if cur:
            BLOCKS[cur] = " ".join(buf).strip()
        cur = m.group(1)
        buf = []
    else:
        buf.append(line.strip())
if cur and buf:
    BLOCKS[cur] = " ".join(buf).strip()

if not BLOCKS:
    raise SystemExit("no narration blocks parsed")
print(f"parsed {len(BLOCKS)} blocks: {list(BLOCKS.keys())}")

Path("audio").mkdir(exist_ok=True)
pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    out = f"audio/{key}.wav"
    sf.write(out, audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:12s} {meta[key]['dur']:6.2f}s  -> {out}")

Path("narration.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
