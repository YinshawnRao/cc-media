#!/usr/bin/env python3
"""Generate female narration wavs for 陈楚生最被低估的5首歌."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SPEED = 1.0
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "提到陈楚生，很多人会先想到《有没有人告诉你》，想到那些一听就能被记住的大歌。但他真正耐听的地方，往往藏在专辑深处。今天这期，我们从第五名往第一名，聊五首最被低估的陈楚生。",
    "p5_xianzhe": "第五名，《先这样吧》。这首放在收尾特别合适，因为歌名本身就很陈楚生。不激烈，不狗血，像一个人已经想了很多，最后只是轻轻说一句，先这样吧。它不如传统情歌容易传播，但成年人感和分寸感很强，适合慢慢听。",
    "p4_bianzheng": "第四名，《辩证关系》。它也来自《侦探C》，冷门感够，概念也够。它不是靠旋律直接抓人的歌，而是把关系里的来回、矛盾和自我拆解唱出来。放在整张合成器风格的专辑里，特别能说明陈楚生不只会写温柔情歌。",
    "p3_sanshiwu": "第三名，《三十五》。这首来自陈楚生和 SPY.C 的《侦探C》。它不是传统的民谣叙事，而是更成熟、更迷离、更有年龄感的自我观察。听这首歌，你会发现他在三十多岁之后，开始把内向、电子和乐队气质揉在一起。",
    "p2_zhuifeng": "第二名，《追风筝的孩子》。在《瘾》这张专辑里，很多人更容易记住《思念一个荒废的名字》，但这首有很典型的陈楚生式少年感。不是热血冲刺，而是有风、有远方，也有一点不肯长大的执拗。",
    "p1_yigeren": "第一名，《一个人唱情歌》。这首来自《冬去春来》，那是他二零零九年的首张国语大碟。相比后来更被路人记住的大歌，它更像专辑开头的一盏小灯：安静、松弛，带一点孤独感。不用力煽情，却特别有陈楚生的叙事气质。",
    "outro": "所以这五首歌的低估，不是因为它们不够好，而是它们太不抢。它们把陈楚生安静、内向、成熟、也有少年感的那一面，藏在旋律和专辑脉络里。真正喜欢他的人，往往会在这些歌里，听见更完整的陈楚生。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:16s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
