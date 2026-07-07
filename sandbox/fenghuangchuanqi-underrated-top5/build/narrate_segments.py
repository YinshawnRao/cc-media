#!/usr/bin/env python3
"""Male narration for 凤凰传奇最被低估的5首歌.

Countdown 5 -> 1 (#1 = 大漠情人, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 凤凰传奇 = 玲花（杨魏玲花，女主唱）+ 曾毅（男 rapper）二人组合。
- 大漠情人 / 传奇 = 首张专辑《月亮之上》(2005) album track；传奇时长 6 分钟以上。
- 康定情缘 = 专辑《吉祥如意》(2007，CD+DVD，西藏实景拍摄官方 MV)。
- 天籁传奇 = 专辑《我从草原来》(2010) album track。
- 中国味道 = 单曲《开门大吉》时期；央视美食节目《中国味道》主题曲，2013 央视春晚演唱。
英文/外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。作品 outro 不得自带投票问句。
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
    "intro": "一说起凤凰传奇，你大概率先想到《月亮之上》《最炫民族风》，想到广场上的神曲。但在这些大热歌背后，他们还藏着不少被严重低估的好歌。今天这期，我们从第五名倒着数，盘一盘凤凰传奇最被低估的五首歌。",
    "p5_zhongguo": "第五名，《中国味道》。比起《开门大吉》那种满屏的节目感，这首没那么容易被路人记住。可它恰恰把喜庆、民族、流行这三种味道，揉成了一首歌：年味、烟火气、还有那股热热闹闹的劲儿，全在里面。它不是最炸的广场舞神曲，却很适合，做这份遗珠榜的开场。",
    "p4_tianlai": "第四名，《天籁传奇》。它来自《我从草原来》，可同一张专辑里有《荷塘月色》这种全民传唱的歌，它就显得低调太多。但这首歌名一点不虚：草原的辽阔、男女声一层一层的铺陈，正是凤凰传奇把民族流行，做得更大、也更亮的一面。",
    "p3_kangding": "第三名，《康定情缘》。同专辑的《自由飞翔》太红，把它压在了下面。可它的民歌底色其实更足，不是简单的副歌循环，而是把地域旋律、男女对唱，和那股标志性的节奏感放在了一起。它更像一首被藏进专辑里的民族小品，耐听，也特别有画面。",
    "p2_chuanqi": "第二名，《传奇》。它同样来自《月亮之上》。六分多钟，不短，也不图一个短平快，气质却非常完整，有一种早期民族流行里少见的史诗感。在一张被同名神曲占满记忆点的专辑里，它最容易被路人跳过。可老粉重听就会发现，它的编曲、段落、还有男女声的配合，野心都很大，撑得起“传奇”这两个字。",
    "p1_damo": "第一名，《大漠情人》。它和《月亮之上》同一张专辑，所以更容易被那首现象级的歌，整个盖住。可它最能代表凤凰传奇早期的那股西域感：有大漠，有远方，有辽阔，也有爱情。这不是最热闹、最炫的凤凰传奇，而是更苍茫、更有故事的那一面。听完这首你会发现，他们从来不只会做广场舞神曲，也能把地域感和流行旋律，结合得这么有味道。",
    "outro": "从《中国味道》到《大漠情人》，这五首歌，没有一首是当年的主打，却各自补上了凤凰传奇最被低估的另一面：苍茫的、辽阔的、有故事的。原来在那些神曲之外，他们一直，都很会唱歌。",
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
