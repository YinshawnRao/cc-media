#!/usr/bin/env python3
"""Male narration for 李健最被低估的5首歌.

Countdown order is 5 -> 1:
深海之寻, 在海上, 抚仙湖, 一辈子的十分钟, 异乡人.

The final CTA is imported from tools/video/outro_cta.py and must remain the
last spoken line.
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
sys.path.insert(0, str(ROOT.parents[1] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zm_yunxi"
SR = 24000

BLOCKS = {
    "intro": (
        "有些歌不靠高音炸场，也不靠热搜出圈。"
        "李健最容易被低估的地方，恰恰是他能把很轻的旋律，唱出很重的时间和生活。"
        "今天从第五名倒数，盘一盘李健最被低估的五首歌。"
    ),
    "p5_shenhai": (
        "第五名，《深海之寻》。这首容易被普通听众漏掉，"
        "但它很能代表李健后期更成熟的审美：更深、更慢，也更有空间感。"
        "它把寻找写得不热血、不焦虑，像一个人往内心更深处潜下去。"
    ),
    "p4_zaaishanghai": (
        "第四名，《在海上》。很多歌写远方，会写得很空；这首不一样。"
        "它真的有一种漂在路上的感觉，孤独不是痛苦，而是一种正在展开的自由。"
        "旋律不是第一耳抓人，却越听越像一部缓慢移动的电影。"
    ),
    "p3_fuxianhu": (
        "第三名，《抚仙湖》。李健很会写地理，但他写的不是旅游风景，"
        "而是把一个地方写成情绪。水面、时间、回忆和人心，都慢慢铺开。"
        "它没有爆点，却有很强的余韵。"
    ),
    "p2_shifenzhong": (
        "第二名，《一辈子的十分钟》。歌名轻轻一句，却有很强的时间感。"
        "它写的不是轰轰烈烈的爱情，而是人生里短暂却很重要的瞬间。"
        "像翻到一张旧照片，突然想起某个再也回不去的十分钟。"
    ),
    "p1_yixiangren": (
        "第一名，《异乡人》。它最适合压轴，因为这首歌真正写出了李健叙事能力的重量。"
        "不用大哭大喊，也能唱出一个人在城市里漂着、忍着、想家的状态。"
        "走了很远，心里还是有一盏回不去的灯。"
    ),
    "outro": (
        "五首歌盘完。第五，深海之寻；第四，在海上；第三，抚仙湖；"
        "第二，一辈子的十分钟；第一，异乡人。"
        "李健被低估的，不是某一种技巧，而是他把克制、诗意和生活重量放在同一首歌里的能力。"
    ),
    "outro_cta": FIXED_OUTRO_CTA,
}

PREFIX_KEYS = {
    "p5_shenhai",
    "p4_zaaishanghai",
    "p3_fuxianhu",
    "p2_shifenzhong",
    "p1_yixiangren",
    "outro",
}


def tts_text(key: str, text: str) -> str:
    # Long isolated Kokoro Chinese segments can drop the first short clause.
    # A natural filler protects the ranking phrase if it leaks into the wav.
    if key in PREFIX_KEYS:
        return "接下来，" + text
    return text


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        spoken = tts_text(key, text)
        chunks = [audio for _, _, audio in pipeline(spoken, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {
            "text": text,
            "tts_text": spoken,
            "dur": round(len(audio) / SR, 3),
        }
        print(f"{key:20s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
