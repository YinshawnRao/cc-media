#!/usr/bin/env python3
"""Male narration for 赵雷最被低估的5首歌.

Countdown 5 -> 1 (#1 = 未给姐姐递出的信, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 《赵小雷》 = 2011-08-07 发行，含 人家(01)/未给姐姐递出的信(02)/画(03)/不开的唇(04)/南方姑娘(06)。
- 《吉姆餐厅》 = 2014-10-19 发行。
- 《无法长大》 = 2016-12-21 发行，含 朵(01)/玛丽(02)/阿刁(03)/鼓楼(04)/成都(06)。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句，逐字不改。
⚠ 长句(~15s+)独立 pipeline() 调用会吞开头第一小句（见 CONVENTIONS.md）：
每首整段旁白前拼一句垫话"接下来，"再合成，垫话本身会被吞掉或偶尔漏出但不影响听感。
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
PAD = "接下来，"  # 垫话防吞字，仅用于长段落（见模块 docstring）

BLOCKS = {
    "intro": "提到赵雷，很多人先想到的，是《成都》《南方姑娘》这些传遍大街小巷的民谣金曲。可翻开他这些年的专辑，你会发现，真正藏得最深的赵雷，往往在那些没被单曲带火的角落里。今天这期，我们从第五名倒数，盘一盘赵雷最被低估的五首歌。",
    "p5_buka": PAD + "第五名，《不开的唇》。它收在二零一一年的《赵小雷》里，同张专辑的记忆点，大多被《南方姑娘》《画》占走，这首歌就成了一首藏在角落里的安静小歌。它唱的是说不出口的东西：有些话不是不想讲，而是到了嘴边，又咽了回去。赵雷最厉害的地方，就是能把这种普通人的沉默，唱得特别具体。它不算最抓耳的旋律，却很适合老粉一个人安静重听。",
    "p4_hadesen": PAD + "第四名，《梦中的哈德森》。它收在二零一四年的《吉姆餐厅》里，那张专辑有《少年锦时》《我们的时光》《理想》这些更响的名字，这首歌就显得低调很多。但它的气质很特别，带着一点异乡感和漂泊感，像一段梦里的河流。它不是典型的赵雷式城市民谣，更像一段旅人的梦境：人还在现实里走着，心却已经漂到更远的地方。",
    "p3_mali": PAD + "第三名，《玛丽》。它来自二零一六年的《无法长大》，同张专辑里《成都》《鼓楼》《阿刁》都更容易被记住，《玛丽》反而像藏在专辑前半段的一首小人物故事。它的好处是特别有画面感：一个名字，一段关系，一种民谣里常见、却一点都不俗套的怀念。赵雷唱这类歌最动人的地方，是不会把人物写成一个符号，而是像真的认识她，真的在某个街口、某段往事里遇见过。",
    "p2_renjia": PAD + "第二名，《人家》。它是二零一一年《赵小雷》的开场曲，歌名很普通，情绪却很赵雷：像站在生活边上，看见别人的日子，也看见自己的空。它不是最容易传唱的民谣金曲，却有一种早期赵雷很珍贵的朴素观察感。没有过度包装，也没有刻意煽情，只是把普通人之间的距离、羡慕和沉默，唱得很淡。越淡，反而越有后劲。",
    "p1_xin": PAD + "第一名，《未给姐姐递出的信》。它同样收在二零一一年的《赵小雷》里，可同张专辑有《南方姑娘》《画》这些更容易被路人记住的作品，把它整个盖了下去。但它其实特别能代表赵雷早期的叙事能力：不是写宏大的远方，而是把一封没递出去的信，一段没说出口的亲情和遗憾，慢慢唱出来。它不靠副歌的爆发取胜，却越听越像一段真实生活里，没来得及说出口的心事。这，才是最被低估的赵雷。",
    "outro": "五首歌盘完。第五，不开的唇；第四，梦中的哈德森；第三，玛丽；第二，人家；第一，未给姐姐递出的信。赵雷从来不只是那个写《成都》《南方姑娘》的民谣代言人，他也很会用最安静、最克制的方式，把普通人的心事唱给你听。这些被大热歌盖住的角落，刚好补全了他最被低估的另一面。",
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
