#!/usr/bin/env python3
"""Male narration for 毛不易最被低估的5首歌.

Countdown 5 -> 1 (#1 = 南一道街, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 5 首全部是毛不易（本名王维家）本人词曲自创 → 可以说"他自己写的"。
- 南一道街 =《平凡的一天》2018；写家乡老街、今昔对比。
- 水乡 / 深夜一角 / 等 =《小王》2020；深夜一角源于他医护实习深夜见闻，等是老唱片质感的再创作。
- 于是没有洗头 =《幼鸟指南》2021（不是 2023），专辑主打之一。
专辑英文名/外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。
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
    "intro": "提到毛不易，很多人先想到的，是《消愁》《像我这样的人》那个写尽普通人心事的创作才子。可在那些大热歌之外，他还有不少被专辑藏起来的好歌，安静、克制，全是他自己写的词曲。今天这期，我们从第五名倒数，盘一盘毛不易最被低估的五首歌。",
    "p5_deng": "第五名，《等》。它收在二零二零年的专辑《小王》里，同张专辑的《一程山路》《呓语》更容易被记住，《等》就显得格外低调。做这张专辑的时候，毛不易给它来了一次最大胆的再创作，刻意做成老唱片的质感，满是旧时光的味道。它唱的，是一种很安静的等待：不是激烈地去追，也不是彻底地放下，而是站在原地，等一个答案，一个人，一个可能不会来的结果。它不算最抓耳，却有一种很慢的后劲。",
    "p4_xitou": "第四名，《于是没有洗头》。它来自二零二一年的专辑《幼鸟指南》，是这张专辑的主打之一。歌名看起来很生活化，甚至有点好笑，可情绪其实特别准：一个人累到连洗头这种小事都懒得去做，生活不是轰然崩塌，而是慢慢失去了整理自己的力气。毛不易最厉害的地方，就是能把这种小小的疲惫，唱得特别真实，最后还轻轻地，和自己和解。",
    "p3_shenye": "第三名，《深夜一角》。它同样收在《小王》里。出道以前，毛不易做过一段医护实习生，那是他最迷茫、也最孤独的日子，深夜下班路上的街角、便利店、路边摊，成了这首歌的灵感。它没有那种大副歌的强刺激，写的却是城市深夜里那些不起眼的普通人：有人在沉默，有人在等，有人把生活默默撑下去。夜色感特别强，适合一个人，安静地重听。",
    "p2_shui": "第二名，《水乡》。它同样来自《小王》，同张专辑里更出圈的那些歌，把它衬成了一处藏在角落的安静风景。毛不易把自己在杭州读书的那段日子，写成了一片江南水乡：水、船、旧地、远方，都不是用力写出来的，而是慢慢浮上来。他唱这种歌特别有优势，声音不急，像一个人坐在岸边，把往事，轻轻讲给风听。",
    "p1_nan": "第一名，《南一道街》。它收在二零一八年的《平凡的一天》里，可同张专辑有《消愁》《像我这样的人》《一荤一素》《借》这些大众记忆更深的作品，很轻易就把它盖了过去。南一道街，是毛不易家乡的一条老街。他没有去写宏大的漂泊，只是把一条街、一段路、一些普通人的日子，慢慢唱出来。日子好像越过越好了，人却没有从前那么快乐。它不靠爆点抓人，却越听越有旧生活的温度。这，就是最被低估的毛不易。",
    "outro": "五首歌盘完。第五，等；第四，于是没有洗头；第三，深夜一角；第二，水乡；第一，南一道街。毛不易最动人的地方，从来都不是炫技，而是替那些说不出口的普通人，把一段段日子，认认真真唱成了歌。这些被大热歌盖住的遗珠，刚好补全了他最安静、也最被低估的另一面。",
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
