#!/usr/bin/env python3
"""Generate concise Chinese narration for the saxophone instrumental ranking.

Foreign song titles and artist names remain visual-only.  Clauses are kept
short so Kokoro does not need a long-line lead-in guard and the forbidden
opening phrase never enters the generated audio.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402


VOICE = "zm_yunxi"
SPEED = 1.05
SR = 24_000
CLAUSE_GAP = 0.10

BLOCKS: dict[str, list[str]] = {
    "intro": [
        "有些乐器，一开口就能把空气变成情绪。",
        "最顶级的五首萨克斯纯音乐，第五名到第一名。",
    ],
    "p5": [
        "第五名。它让萨克斯先放下深情，开始真正地摇摆。",
        "厚实暖音色配上松弛律动，身体会比耳朵先听懂。",
    ],
    "p4": [
        "第四名。钢琴和弦乐把空间铺开，萨克斯像一段没有歌词的告白。",
        "浪漫，却始终保留克制。",
    ],
    "p3": [
        "第三名。吉他铺开城市夜色，萨克斯慢慢说出心事。",
        "慵懒，性感，又带一点危险。",
    ],
    "p2": [
        "第二名。旋律一响，黄昏、归途和一天结束后的画面都回来了。",
        "它把回家，变成所有人都听得懂的声音。",
    ],
    "p1": [
        "第一名。没有复杂铺垫，旋律像一束光直接进入耳朵。",
        "简单，温暖，又带一点孤独。它就是现代萨克斯最接近标准答案的一首。",
    ],
    "outro": [
        "从松弛律动到浪漫告白，从城市夜色到归途和孤独。",
        "萨克斯不用一句歌词，也能让每个人听见自己的故事。",
    ],
    "outro_cta": [FIXED_OUTRO_CTA],
}


def synthesize_clause(pipeline: KPipeline, text: str) -> np.ndarray:
    chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
    return chunks[0] if len(chunks) == 1 else np.concatenate(chunks)


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta: dict[str, dict[str, object]] = {}
    silence = np.zeros(round(SR * CLAUSE_GAP), dtype=np.float32)

    for key, clauses in BLOCKS.items():
        pieces: list[np.ndarray] = []
        clause_durations: list[float] = []
        for index, clause in enumerate(clauses):
            audio = synthesize_clause(pipeline, clause)
            pieces.append(audio)
            clause_durations.append(round(len(audio) / SR, 3))
            if index + 1 < len(clauses):
                pieces.append(silence)
        samples = pieces[0] if len(pieces) == 1 else np.concatenate(pieces)
        output = AUDIO / f"{key}.wav"
        sf.write(output, samples, SR)
        meta[key] = {
            "text": "".join(clauses),
            "clauses": clauses,
            "clause_durations": clause_durations,
            "voice": VOICE,
            "speed": SPEED,
            "duration": round(len(samples) / SR, 3),
        }
        print(f"{key:12s} {meta[key]['duration']:6.2f}s  {output}")

    (ROOT / "narration.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("TOTAL narration", round(sum(float(v["duration"]) for v in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
