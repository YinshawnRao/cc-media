#!/usr/bin/env python3
"""Male narration for 丁世光最被低估的5首歌.

Countdown 5 -> 1, preserving the user ranking:
1 不散的筵席, 2 如果我们当时一起会怎么样, 3 月食, 4 你的家, 5 乌托邦.
The video reveals from #5 to #1.
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

# Protect longer standalone Kokoro zh calls from dropping the first phrase.
LEAD_GUARD = "接下来，"
LEAD_GUARD_OVERRIDE = {"intro": "今天，", "outro": "那，"}

BLOCKS = {
    "intro": "提到丁世光，很多人会先想到《神探》《Simon》这些被乐迷反复提起的作品。可真正耐听的部分，往往不在最响的歌单里，而在那些情绪更安静、审美更完整、需要多听几遍才回来的歌里。今天这期，我们从第五名倒数，盘一盘丁世光最被低估的五首歌。",
    "p5_wutuobang": "第五名，《乌托邦》。这首很适合放在开场，因为它不是丁世光最典型的忧伤路线，而是更明亮、更自由、更有逃离现实感。很多人记得他的细腻和克制，却容易忽略他也能写出轻盈、浪漫、有异域色彩的作品。《乌托邦》不算最红，但它能证明，丁世光的音乐审美从来不窄。",
    "p4_nidejia": "第四名，《你的家》。丁世光写爱情很拿手，但这首把视角转向亲情和成长，反而更显珍贵。它不是直接煽泪的家庭歌，而是一个人长大以后，慢慢听懂父辈沉默里的重量。它被低估，是因为情绪太安静，不像热门情歌那么容易传播，可越往后听，越像是在说：我终于懂了你。",
    "p3_yueshi": "第三名，《月食》。这首很有丁世光的听觉电影感，它不是简单写爱情变暗，而是把关系里的遮蔽、拉扯和失衡，写成一场天文现象。旋律有画面，编曲也有空间，像一个镜头一点点暗下去。它没有特别用力的爆点，却完整地唱出了两个人的光，怎样慢慢被挡住。",
    "p2_ruguo": "第二名，《如果我们当时一起会怎么样》。歌名已经把遗憾写完了，但歌本身没有落进普通伤感情歌的套路。它最动人的地方，是那种假设感：不是哭诉分开，而是在想另一条人生支线。如果当时做了不同选择，现在会不会不一样。放在《神经志》里，它可能没有《Simon》《神探》那么容易被记住，却更适合深夜反复听。",
    "p1_busandeyanxi": "第一名，《不散的筵席》。它不是丁世光最常被拿出来讨论的歌，却很能代表他最动人的一面：不靠大开大合，只把分别写得体面又克制。歌名像一句安慰，听完却有很强后劲。它真正厉害的地方，是把离别唱得不狗血，像电影散场后，还留在座位上的那个人。",
    "outro": "五首歌盘完。第五，乌托邦；第四，你的家；第三，月食；第二，如果我们当时一起会怎么样；第一，不散的筵席。丁世光最被低估的地方，也许不是某一首歌没红，而是他总能把复杂情绪唱得很轻，却让后劲留得很久。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        guard = LEAD_GUARD_OVERRIDE.get(key, LEAD_GUARD)
        synth_text = text if key == "outro_cta" else guard + text
        chunks = [audio for _, _, audio in pipeline(synth_text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:22s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
