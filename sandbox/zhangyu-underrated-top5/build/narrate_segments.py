#!/usr/bin/env python3
"""Male narration for 张宇最被低估的5首歌."""
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
        "张宇的大热歌太多，很多人一提他，先想到《用心良苦》《雨一直下》《曲终人散》。"
        "但老粉会反复听的，往往藏在专辑深处。"
        "今天从第五名倒数，盘一盘张宇最被低估的五首歌。"
    ),
    "p5_shuogushi": (
        "第五名，《说故事》。它来自《单恋》，同专辑《单恋一枝花》更容易被记住。"
        "这首好在叙事感：不急着把情绪砸出来，而像坐下来慢慢讲一段关系。"
        "讲到最后才发现，故事里最难受的人，其实是自己。"
    ),
    "p4_xinjing": (
        "第四名，《心井》。它来自《消息》，歌名本身就有画面：心里像有一口井，话掉下去，回声很深，却没人真正听见。"
        "它不是爆发型苦情歌，而是更内收、更暗的一首，特别适合张宇那种沙哑和沧桑。"
    ),
    "p3_qianjin": (
        "第三名，《千金难买》。来自《整个八月》，旋律线更长，情绪也更厚。"
        "它唱的是有些东西再珍贵、再想要，也不是用代价就能换回来。"
        "张宇和十一郎把后悔写得很沉，却不廉价。"
    ),
    "p2_shaogeren": (
        "第二名，《不过少个人来爱》。名字听起来像一句轻描淡写的话，但好听的地方正是这种装作没事。"
        "不是撕心裂肺地说失去，而是故作轻松地说，不过就是少个人来爱。"
        "声音越像硬撑，情绪越往下沉。"
    ),
    "p1_yuanhuang": (
        "第一名，《圆谎》。它收录在《消息》里，被《消息》和《曲终人散》这种更容易被记住的作品盖住。"
        "但它特别张宇：明知道关系有裂缝，还要替对方、也替自己把谎说圆。"
        "十一郎的词很狠，张宇的嗓音把自欺欺人的痛唱得很真。"
    ),
    "outro": (
        "五首歌盘完。第五，说故事；第四，心井；第三，千金难买；第二，不过少个人来爱；第一，圆谎。"
        "张宇最被低估的，不只是几首遗珠，而是他和十一郎在那些没被大热光环照到的地方，写过更沉、更拧、也更耐听的爱情。"
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
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
