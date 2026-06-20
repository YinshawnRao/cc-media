#!/usr/bin/env python3
"""Generate female narration wavs for the Liang Jingru saddest top 5 video."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "梁静茹的情歌，唱的从来不是热恋，而是爱情里最苦的那一面。这五首，我们先不公布完整排名，从第五名开始，一首一首往回数，看她到底把哪一种苦，唱进了多少人心里。",
    "huiguoqu": "第五名，《会过去的》。它表面上是一首疗愈的歌，其实藏得很深。因为它不是已经好了，而是我知道总有一天会好，但是现在，还没有。失去一个人之后，一个人慢慢收拾往事，越平静，越疼。",
    "chongbai": "第四名，《崇拜》。这首苦在不对等。把对方放得太高，把自己放得太低，最后才发现，那不是爱情里的平等，而是一种近乎卑微的仰望。它更像一场清醒之后的自嘲，原来我曾经，那么用力地相信你。",
    "manleng": "第三名，《慢冷》。它是那种后劲型的苦，不一定在分手当下最痛，而是越往后越痛。别人已经转身了，你才慢慢反应过来，原来真的失去了。有些人不会当场崩溃，只是慢慢冷掉，慢慢把自己，困在回忆里。",
    "kexi": "第二名，《可惜不是你》。这是遗憾系的天花板。不是爱得不够，也不是谁特别坏，而是曾经那么接近，最后陪在身边的，却不是那个人。它苦在差一点，差一点圆满，差一点，就是永远。",
    "huxi": "第一名，《会呼吸的痛》。它最狠的地方，不是分手那一刻，而是分开以后，一个人还要替两个人，把曾经想象过的生活继续过完。走路会想，吃饭会想，去到某个地方，也会想。它把想念，写成了一种会呼吸的，身体反应。",
    "outro": "最后，复习一下这份榜单。第五，《会过去的》。第四，《崇拜》。第三，《慢冷》。第二，《可惜不是你》。第一，《会呼吸的痛》。梁静茹最苦的，从来不是撕心裂肺的那一种，而是平静底下，藏了很多年，也没有真正过去的那一种。",
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
        print(f"{key:10s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
