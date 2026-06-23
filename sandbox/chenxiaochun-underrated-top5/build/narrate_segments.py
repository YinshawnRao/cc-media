#!/usr/bin/env python3
"""Male narration for 陈小春最被低估的5首歌.

Countdown order is 5 -> 1. The final CTA is imported from tools/video/outro_cta.py
because it is a repo-level convention. English album names (That's Mine / Sing) are
kept OUT of the spoken text (Kokoro 中英混读 reads them awkwardly) and live only in
the on-screen meta labels.
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
    "intro": "提到陈小春，很多人先想到的，是山鸡哥，是古惑仔，是那个又凶又痞的硬汉。可他的情歌里，藏着另一面，粗粝、卑微，也意外地深情。今天这期，我们从第五名倒数，盘一盘陈小春最被低估的五首歌。",
    "p5_buzai": "第五名，《不在服务区》。它来自《独家记忆》，可同张专辑里《独家记忆》太强，把它整个盖了过去。它写的不是不爱了，而是更现代的一种失落，联系不上，等不到回应，对方像突然从你的生活里断了线。陈小春没有声嘶力竭，却把成年人关系里那种无力感，唱得特别真。",
    "p4_fengliu": "第四名，《风流》。这是陈小春粤语歌里，很值得重听的一首。它不像《相依为命》《乱世巨星》那样有强烈的大众标签，却特别能体现他身上那股江湖气、男人味，还有一点玩世不恭。它不是传统的苦情歌，而是更潇洒、更有人物感，看起来满不在乎，其实心里都是事。",
    "p3_yaren": "第三名，《哑忍》。它收在陈小春十年纪念的那张精选里，不是随便凑数的一首。这首歌的关键词，是忍，不爆发，也不控诉，而是把委屈和不甘，硬生生地压下去。陈小春的声音本来就带点沙哑和倔强，唱这种忍着不说的状态，特别有画面感。",
    "p2_xiabanbeizi": "第二名，《下半辈子》。比起《独家记忆》那种一听就哭的大歌，它更生活，也更沉。它打动人的地方，不是反复说我有多爱你，而是把后半生的重量，放进一句承诺里。陈小春唱深情最厉害的一点，就是不甜，却很真，像一个人用了很久，才终于学会认真。",
    "p1_xianshi": "第一名，《献世》。它来自《夜生活》，可同张专辑里《相依为命》太强，大众的记忆几乎全被那首占满，《献世》反而像藏在后面的一道暗伤。它最狠的地方不是苦，而是卑微到几乎自嘲，明知道自己不体面，还是放不下。陈小春唱这种歌特别有味道，不靠漂亮的音色，靠的是那种粗粝、难堪、认输之后还嘴硬的真实。",
    "outro": "五首歌盘完。第五，不在服务区；第四，风流；第三，哑忍；第二，下半辈子；第一，献世。陈小春从来不只是那个又凶又痞的山鸡哥，他的情歌里，有江湖男人很少示人的卑微、脆弱和深情。这些被大热歌盖住的遗珠，刚好补全了他更复杂的另一面。",
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
