#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。

主题＝华晨宇最被低估的5首歌（遗珠盘点），揭晓序 5→1。
最后一段固定为 outro_cta（引流 CTA，硬约束、优先级高于 brief，见 CONVENTIONS「固定结尾配音」）。
注意：Kokoro 中英混读差 → 旁白不照念英文歌名《Let You Go》，说"这首英文小歌"，屏幕卡片仍显示英文。
"""
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
    "intro": "提到华晨宇，很多人先想到的是高音，是炸裂的现场。但在他的歌单里，其实藏着一批没那么吵、却越听越有味道的遗珠。今天这五首，都被严重低估，我们从第五名开始。",
    # 倒数揭晓 5 → 1
    "p5_letyougo": "第五名，来自他的第一张专辑《卡西莫多的礼物》。同一张专辑里，《烟火里的尘埃》更容易被记住，这首英文小歌的存在感一直偏低。但它把放手这件事，唱得有点漂浮、有点空，不是用力宣泄，而是轻轻松开。路人可能不会主动点开，可一旦回头再听，就会发现它特别耐听。",
    "p4_xiaoshi": "第四名，《消失的昨天》，藏在专辑《H》里。它不像那些最出圈的作品，靠高压和爆发抓人，而是更偏情绪的回望。昨天消失了，人却还站在原地，像是在和一段过去慢慢告别。它不抢，可旋律和情绪都很完整，越重听越上头。",
    "p3_zaowuzhe": "第三名，《造物者》，被低估得相当明显。同样在《H》里，它没有话题度，也不靠概念取巧，却很有华晨宇那种世界观气质。有一点冷，有一点俯瞰，藏着对生命和创造的想象。它不是爆款脸，却是真爱粉会单独拎出来说，这首其实很有东西的那一首。",
    "p2_weiguang": "第二名，《微光》。在《卡西莫多的礼物》里，大家更容易记住同名曲，但《微光》才是最适合做遗珠的那一首。它没有强烈的戏剧外壳，更多是温柔、明亮，带着一点治愈。华晨宇早期最难得的地方，是他不只会唱怪和炸，也能把这种细小的光，唱得一点都不廉价。",
    "p1_wligj": "第一名，《我离孤单几公里》，同样收录在专辑《H》。比起同专辑里更常被讨论的那些歌，它更像藏在专辑最深处的一段独白。它不是最炸的那一类，而是把孤独、远行、还有回头无路的感觉，唱得特别具体。越安静，越有后劲。这也是我把它放在第一名的原因。",
    # 作品自身 outro：内容总结 + 主题升华，收在歌手特质上。**不带投票问句**（交给固定 CTA，否则双 CTA）。
    "outro": "这五首，从首专的遗珠，到《H》里的隐藏款，都没有站在华晨宇最聚光的地方。但被低估，从来都不等于不够好。有时候，恰恰是这些安静的歌，最经得起一遍又一遍地重听。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（见 outro_cta.py / CONVENTIONS「固定结尾配音」）。
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        sf.write(AUDIO / f"{key}.wav", audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:14s} {meta[key]['dur']:6.2f}s")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
