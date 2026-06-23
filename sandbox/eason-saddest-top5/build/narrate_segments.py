#!/usr/bin/env python3
"""Generate narration wavs for 陈奕迅最苦的5首歌.

Default repo voice policy: male Chinese voice zm_yunxi unless the brief asks for female.
The opening keeps the full list hidden; the outro reveals it and then appends the fixed CTA.
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "陈奕迅的苦，不靠大哭大喊。很多时候，他只是把一句放不下，唱得像已经想通了。今天这五首，我们不先摊开歌单，从第五名开始，往第一名数。",
    "putao": "第五名，《葡萄成熟时》。它的苦不在爆发，而在熬。黄伟文写的不是别痛了，而是痛也有自己的季节。有些遗憾不会马上给你答案，你只能先活着，等它慢慢变成别的东西。",
    "sunyou": "第四名，《最佳损友》。这首一定要进来，因为友情走散，比爱情失恋更难开口。恋人分开，还能说一句不合适。朋友散了，往往没有仪式，没有告别，甚至连难过都显得矫情。",
    "renlai": "第三名，《人来人往》。世界很热闹，可真正留下的人没几个。它不只是写爱情，也写关系里的流动性。你以为某个人会是例外，最后发现，他也只是人来人往里的一个。",
    "mingnian": "第二名，《明年今日》。它厉害在，不写刚分手那一下，而是把一年、十年，甚至更久以后都唱进来。最狠的不是分开，是你已经想象到，对方未来的人生里没有你。",
    "fushi": "第一名，《富士山下》。爱而不得的最高级，不是纠缠，是承认自己搬不走那座山。林夕把失恋写成一种修行。你可以喜欢，可以远远看着，但你终于学会，不把它占为己有。",
    "outro": "最后完整揭晓这份榜单。第五，《葡萄成熟时》。第四，《最佳损友》。第三，《人来人往》。第二，《明年今日》。第一，《富士山下》。陈奕迅最苦的歌，往往不是让你哭出来，而是让你在很多年后，突然懂了自己为什么放不下。",
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3), "voice": VOICE}
        print(f"{key:12s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()

