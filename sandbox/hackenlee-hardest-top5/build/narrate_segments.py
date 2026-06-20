#!/usr/bin/env python3
"""Generate female narration wavs for the Hacken Lee hardest top 5 video."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

FIXED_OUTRO_CTA = "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。"

BLOCKS = {
    "intro": "李克勤常被叫做零瑕疵歌手，稳、准、清楚，像唱片一样。但越是这种歌手，越能看出真正的难度。今天这五首，不只看高音，而是看节奏、咬字、气息、线条和现场稳定。我们从第五名开始，一首一首听。",
    "p5_gaomei": "第五名，《高妹》。它收在《Custom Made》时期，梁咏琪作曲，李克勤自己填词。难点不是传统高音，而是节奏感、轻快咬字和换气位置。要唱得俏皮、有态度，还不能赶拍；一急，就从高妹唱成了赶地铁。",
    "p4_feihua": "第四名，《飞花》。这首歌难，不是猛冲，而是副歌连续的高位旋律要一直柔、一直稳、一直干净。绵绵头上飞花，看起来顺口，其实非常吃气息均匀、尾音控制和粤语轻重。唱太实，雪花变石头；唱太飘，又没支点。",
    "p3_yueban": "第三名，《月半小夜曲》。它不是最高，但极难唱好。长线条、弱声、尾音、气息和音准，几乎每一样都在考人。最麻烦的是情绪分寸：唱重了俗，唱轻了虚，要有那种像小提琴一样，如泣如诉的弧线。",
    "p2_dahuitang": "第二名，《大会堂演奏厅》。这首是李克勤很早期的粤语代表作，歌词密，叠字多，句子推进又快。难就难在，字头要清、节奏要准，旋律还得保持端正和深情。听起来优雅，唱起来就是咬字和体能双杀。",
    "p1_buhui": "第一名，《我不会唱歌》。这首的难点非常硬核，旋律灵感来自李斯特《钟》，编曲里有大量钢琴演奏段落。唱它最难的是跟钢琴的速度、切分和跳跃一起走：每一句都要卡准，高位句子要稳，字头还要清楚，不能被钢琴牵着跑飞。",
    "outro": "再回顾一次这份榜单：第五《高妹》，第四《飞花》，第三《月半小夜曲》，第二《大会堂演奏厅》，第一《我不会唱歌》。李克勤的难，从来不是单纯炫高，而是把速度、咬字、气息和音准，都唱到像没有难度一样。",
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
