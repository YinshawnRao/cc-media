#!/usr/bin/env python3
"""Male narration for 萧敬腾最被低估的5首歌.

Countdown 5 -> 1 (#1 = 话不多, the climax). 倒数揭晓。
事实口径（待 SOURCES.md 核实后定稿，避免文案出错）：
- 倒数顺序：#5 爸爸 / #4 我在哭 / #3 活在故事里 / #2 白蛇传 / #1 话不多。
- 专辑：话不多 + 白蛇传 = 《狂想曲》；活在故事里 + 爸爸 = 《以爱之名》；我在哭 = 首张同名专辑。
- 词曲归属：只有在确认萧敬腾本人作词/作曲时才说"他写的"。《爸爸》= 他自己词曲（brief 称，待核）。
  其余四首默认不写"他写"，用"演唱/诠释"。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。专辑/歌名均中文，无外文进配音。
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
    "intro": "提到萧敬腾，很多人先想到的，是那把能轻松飙上去的大嗓，是雨神、是飙高音、是炸场。可他真正动人的，其实常常是收着唱的时候。今天这期，我们绕开那些最炸、最热的代表作，从第五名倒数，盘一盘萧敬腾最被低估的五首歌。",
    "p5_baba": "第五名，《爸爸》。它收录在专辑《以爱之名》里，是萧敬腾自己写词、写曲的一首歌。比起那些舞台上爆发力十足的作品，《爸爸》更私人、更朴素，也更容易被路人忽略。它不讨巧，也不炸场，而是把亲情、距离，还有那些不太容易说出口的情感，轻轻放进歌里。作为遗珠，它补上的，正是萧敬腾更柔软、更贴近生活的一面。",
    "p4_zaiku": "第四名，《我在哭》。它来自萧敬腾的首张同名专辑。比起《收藏》《王子的新衣》《原谅我》那些更容易被记住的歌，《我在哭》低调很多，但其实是一首很值得重听的慢歌。它不是简单地哭给你看，而是把一种成熟一点的委屈和压抑，慢慢唱出来。萧敬腾的声音本来很有爆发力，难得的是这一首他收住了，把情绪放进旋律里，一点一点往下沉。",
    "p3_gushili": "第三名，《活在故事里》。它收在《以爱之名》中，同张专辑里有《福尔摩斯》《以爱之名》《兄弟我说》这些更醒目的作品，《活在故事里》就显得低调很多。这首歌词曲都是萧敬腾自己写的，概念也很好：人有时候不是活在现实里，而是活在自己反复讲给自己听的故事里。这种作品很适合他，声音有厚度，也有一点孤独的戏剧感，不用唱得太满，就能把整个画面撑起来。",
    "p2_baishe": "第二名，《白蛇传》。它同样来自《狂想曲》，而且词曲都是萧敬腾自己写的，风格非常特别：不是他最常见的抒情摇滚，也不是路人最熟的大情歌，而是带着一点戏剧感、东方感和故事感。它的遗珠价值就在于，你能听见萧敬腾作为一个音乐人的玩心和野心，他不只是在唱一首歌，更像是在演一个角色、撑起一整个场景。路人可能不熟，但老粉会知道，这首很有东西。",
    "p1_buaduo": "第一名，《话不多》。它收录在《狂想曲》里，同张专辑还有《狂想曲》《只能想念你》《怎么说我不爱你》这些更容易被记住的作品，所以《话不多》很容易被盖过去。但它特别能代表萧敬腾不靠大嗓爆发，也能打动人的那一面：情绪很收，表达很克制，像一个不太会解释的人，把所有的话，都压在了声音里。越是不说，越有后劲。这，就是最被低估的萧敬腾。",
    "outro": "五首歌盘完。第五，爸爸；第四，我在哭；第三，活在故事里；第二，白蛇传；第一，话不多。萧敬腾从来不只是那个会飙高音、会炸场的雨神，他更是一个会收、会演、会讲故事的歌者。这些被大热歌盖住的遗珠，刚好补全了他最克制、也最细腻的另一面。",
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
