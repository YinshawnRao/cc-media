#!/usr/bin/env python3
"""Female narration for 张信哲最被低估的5首歌.

Countdown order is 5 -> 1. The final CTA is imported from tools/video/outro_cta.py
because it is a repo-level convention.
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

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到张信哲，很多人第一反应是《过火》《爱如潮水》《信仰》。可阿哲真正耐听的地方，不只在那些全民大歌里。今天这期，我们从第五名倒数，聊五首被低估的张信哲遗珠。",
    "p5_kong": "第五名，《空出来的时间刚好拿来寂寞》。这首很适合补上中后期阿哲被低估的一面。它不是传统的苦情大歌，更像城市里一个人和自己对话。资料里说它写的是城市人的无声叛逆，歌名像深夜文案，但歌本身很有质感。",
    "p4_fei": "第四名，《你应该飞的》。同在《做你的男人》这张专辑里，它常常被前面几首歌盖住。陈小霞和姚若龙这组很会写温柔里的痛，这首不是占有式情歌，而是明明舍不得你，却还是唱出，你应该去更远的地方。",
    "p3_shuohuang": "第三名，《说谎》。不是林宥嘉那首，是张信哲《做你的男人》里的《说谎》。这张专辑更容易被记住的是同名歌，但资料里其实把《说谎》称为许久没有出现的标志性好歌。它的苦不是大哭，是明知道对方在说谎，自己还一直替关系找台阶。",
    "p2_xiayong": "第二名，《下一个永远》。这首被《白月光》的光环盖住太明显。同名专辑第一波主打是《白月光》，但这首同名曲其实很强。资料里提到它从低吟式开场到副歌高音转折，都很有电影画面感，是被同专辑大歌压住的正经遗珠。",
    "p1_xinqing": "第一名，《心情卡片》。这首我会放第一。它来自《直觉》，不是路人最常点名的阿哲金曲，却特别能体现他转入新力以后，那种更清新、更都市的表达。高音流畅，情绪真诚，听完有一种郁闷被扫开的感觉。粉丝懂，但大众歌单里太少见。",
    "outro": "这就是这一期，张信哲最被低估的五首歌。从第五到第一：空出来的时间刚好拿来寂寞，你应该飞的，说谎，下一个永远，和第一名心情卡片。阿哲最动人的，不只是高音和金曲，而是这些被大歌挡住的角落里，也有完整的城市、告别和温柔。",
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
        print(f"{key:15s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
