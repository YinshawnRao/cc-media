#!/usr/bin/env python3
"""Narration for 李宇春最被低估的5首歌.

Countdown order is 5 -> 1:
小宇宙, 冷暖, 似火年华, 一而再再而三地喜欢你, 西门少年.

The final CTA is imported from tools/video/outro_cta.py and must remain the
last spoken line.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
sys.path.insert(0, str(ROOT.parents[1] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zm_yunxi"
SR = 24000


def guard(text: str) -> str:
    """Protect long standalone Kokoro segments from swallowing the first phrase."""
    return "接下来，" + text


BLOCKS = {
    "intro": (
        "有些歌手的代表作太亮，反而会把更耐听的歌藏起来。"
        "李宇春就是这样。她有舞台、有态度，也有很多没有被充分讨论的细腻表达。"
        "今天从第五名倒数，盘一盘李宇春最被低估的五首歌。"
    ),
    "p5_xiaoyuzhou": guard(
        "第五名，《小宇宙》。它适合作为开场，因为它不生僻，也不晦涩，"
        "但一直没有被放进更大的讨论里。早期李宇春身上那种轻盈、独立、带一点倔强的能量，"
        "都藏在这首歌里。"
    ),
    "p4_lengnuan": guard(
        "第四名，《冷暖》。这首歌不靠高音爆发，也不靠强情绪推进。"
        "它的低估点，恰恰是那种冷感质地和成熟表达。"
        "情绪不炸，但后劲很强，越听越能听见她对关系和自我的克制判断。"
    ),
    "p3_sihuo": guard(
        "第三名，《似火年华》。它很容易被《再不疯狂我们就老了》这张专辑的主概念盖住，"
        "但单独听，特别有青春电影感。它不是热血鸡汤，"
        "而是明知道时间会过去，也承认自己认真燃烧过。"
    ),
    "p2_yierzai": guard(
        "第二名，《一而再再而三地喜欢你》。这首歌打破了很多人对李宇春只酷不柔软的刻板印象。"
        "它不靠舞台爆发，也不靠重节奏，而是把喜欢写得很轻、很日常、很耐听。"
        "这份温柔，其实很珍贵。"
    ),
    "p1_ximenshaonian": guard(
        "第一名，《西门少年》。它最适合压轴，因为这不是简单讲成长，"
        "而是把成都出发、被争议凝视、一路走到今天的经历，写成一次自我回望。"
        "个人叙事浓度很高，也最能解释，为什么李宇春的酷从来不是表面姿态。"
    ),
    "outro": (
        "五首歌盘完。第五，小宇宙；第四，冷暖；第三，似火年华；"
        "第二，一而再再而三地喜欢你；第一，西门少年。"
        "李宇春被低估的，不只是某几首歌，而是她在锋利、温柔、冷感和自我叙事之间，"
        "一直保留的那条个人线索。"
    ),
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:20s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
