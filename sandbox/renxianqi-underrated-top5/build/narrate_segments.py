#!/usr/bin/env python3
"""Narration for 任贤齐最被低估的5首歌.

Countdown order is 5 -> 1. The final CTA is imported from the repo-level
convention so the wording stays consistent across episodes.
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

BLOCKS = {
    "intro": "任贤齐的大歌太多了，很多歌一出来，就是一代人的记忆。但也正因为这些歌太强，有些耐听的侧面，反而被埋在专辑深处。今天这期，从第五名倒数，聊小齐最被低估的五首歌。",
    "p5_aishangle": "第五名，《爱伤了》。它不像《心太软》那样一听就被全民记住，也没有江湖味、兄弟感这些标签。它更像一首低调的伤感慢歌。爱真的伤到了，人才会安静下来。",
    "p4_yuedinglantian": "第四名，《约定蓝天》。这首来自《老地方》。那张专辑是小齐加入 EMI 后的首张个人专辑，尝试很多。同名歌更容易被记住，但《约定蓝天》有一种开阔感，不是苦到最后，而是还愿意往前看。",
    "p3_xinqingchezhan": "第三名，《心情车站》。它被《爱像太平洋》那一批大歌压得很明显。没有《伤心太平洋》的戏剧感，也没有《对面的女孩看过来》的传唱度，但它像人在车站停一下，整理心情，再继续往前走。",
    "p2_bieku": "第二名，《别哭》。同样来自《爱像太平洋》，遗珠感很强。它不是大开大合的悲伤，而是很朴素地安慰一个人。小齐最打动人的地方，有时就是这种，我知道你难过，但我会陪着你的生活感。",
    "p1_anjing": "第一名，《安静的人》。这首我会放第一。它也在《爱像太平洋》里，旁边全是国民级大歌，所以特别容易被忽略。但它更沉、更孤独、更内向，真爱粉重听，会发现它很耐听。",
    "outro": "这一期的五首遗珠，其实刚好拼出了任贤齐不那么热闹的一面。不是只有江湖、兄弟和邻家男孩，他也能唱沉默、安慰、停顿和重新出发。这些歌没有被传唱到最大声，但值得被重新听见。",
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
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
