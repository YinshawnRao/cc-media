#!/usr/bin/env python3
"""Generate female narration wavs for the Sandy Lam (林忆莲) underrated top 5 video."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "提到林忆莲，很多人先想到的是《至少还有你》这种全民传唱的大歌。但她最高级的部分，常常藏在没被传开的歌里。这一期，我们不聊代表作，只挑五首被低估的遗珠。先不公布完整排名，从第五名开始，一首一首往前听，最后再一起揭晓。",
    "p5_taiyangxi": "第五名，《太阳系》。这是新时期林忆莲的一个隐藏款。在那张让大家讨论最多的是《沙文》《纤维》的专辑里，《太阳系》几乎没什么存在感。可它特别能代表这张唱片的气质，空灵、电子，带着一点宇宙般的距离感。她用气声去唱，把人和人之间那种又互相吸引、又互相排斥的关系，写得很轻，也很迷人。",
    "p4_liyou": "第四名，《理由》。它来自专辑《铿锵玫瑰》。同名主打太有时代女性的符号感，光芒太盛，《理由》就很容易被盖过去。但这一首其实很值得重听。它没有《铿锵玫瑰》那么外放，而是更内在、更冷静，像一个人在一段关系里，终于把话想清楚了。不是用力的洒脱，而是成熟之后，安安静静地把自己重新整理了一遍。",
    "p3_wozuo": "第三名，《我坐在这里》。这首被夹在《至少还有你》《失踪》这些更常被提起的歌中间，路人很容易就把它忽略掉。但它有一种很冷的都市孤独感。不是哭着喊我好惨，而是我就坐在这里，看着一切慢慢离我远去。林忆莲唱这种克制的疏离，特别厉害，越是不把情绪往外推，听完越是后劲很大。",
    "p2_feide": "第二名，《飞的理由》。它和《至少还有你》出自同一张专辑，可那首后来成了她演唱会的必唱金曲，光环实在太强，《飞的理由》的记忆点就弱了很多。它其实是电视剧《人间四月天》的主题曲。好就好在它一点都不煽情，旋律有一种轻轻升起来的感觉，像一个人在很安静地告别，也在很安静地，重新出发。",
    "p1_meiyou": "第一名，《没有发生的爱情》。它来自那张被反复重估的概念专辑《野花》。整张唱片用花来串联，写的是现代东方女性的心路，而这一首，对应的是昙花。《野花》当年因为太不商业、太实验，刚发行时反响平平，后来才被一再重新发现，是真正意义上的艺术遗珠。这首歌唱的不是撕心裂肺的苦，而是还没开始，就已经错过的那种空白。很淡，却很高级。",
    "outro": "最后，把这一期的排名一起理一遍。第五，《太阳系》；第四，《理由》；第三，《我坐在这里》；第二，《飞的理由》；第一，《没有发生的爱情》。林忆莲被低估的，从来不是唱功，而是这种把克制、疏离和留白都唱得这么高级的本事。她最好的歌，很多都没大红，可时间越久，越有人懂。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（见 tools/video/outro_cta.py / CONVENTIONS「固定结尾配音」）。
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
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
