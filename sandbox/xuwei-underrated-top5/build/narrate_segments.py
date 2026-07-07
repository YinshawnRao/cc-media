#!/usr/bin/env python3
"""Male narration for 许巍最被低估的5首歌.

Countdown 5 -> 1 (#1 = 天鹅之旅, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 五首全部由许巍一人作词、作曲、演唱（创作型歌手，无合作词曲）。
- 天鹅之旅 = 2002《时光·漫步》开场第1首（同张大歌 蓝莲花/完美生活/礼物）。
- 九月 / 简单 = 2000《那一年》（许巍第一次自己包办词曲唱+制作）。
- 夏日的风 = 2002《时光·漫步》第9首。
- 故事 = 2008《爱如少年》第3首（13首）。⚠️不要说"第五张专辑"（实为第6张，2006《在路上》常被漏算）。
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
    "intro": "提到许巍，很多人脑子里先响起的，是《蓝莲花》《故乡》那种辽阔的声音，是一代人心里那个唱着远方和理想的摇滚诗人。可在那些被唱到街知巷闻的大歌之外，他还有不少被盖住的好歌，更安静、更松弛，像他在喧嚣落定之后，轻轻说给自己听的话。今天这期，我们从第五名倒数，盘一盘许巍最被低估的五首歌。",
    "p5_gushi": "第五名，《故事》。它收在二零零八年的《爱如少年》里，可那张专辑的记忆点，几乎被《爱》《彩云之巅》《家》占满了，《故事》就显得安静了许多。它没有那种炸开的副歌，更像一首慢慢讲述的叙事歌，许巍坐下来，把一段人生轻轻说给你听。它不抢耳，却很耐听，是中后期许巍少见的、那种温暖又沉静的一面。",
    "p4_xiari": "第四名，《夏日的风》。它同样来自二零零二年的《时光·漫步》，可同张的《蓝莲花》《完美生活》太强，这首就被衬得很低调。但它特别适合放进遗珠榜：不是典型的那种许巍式的远方，而是更轻、更暖、更有生活气息的一首。歌名就像一阵从夏天吹来的风，不激烈，不沉重，却能听见他声音里少见的松弛和明亮。",
    "p3_jiandan": "第三名，《简单》。它也来自《那一年》，没有《故乡》那样的国民度，也没有标题曲的光环，但它在许巍的作品里很特别：旋律和编曲带着更轻、也更迷幻的气质，情绪没有那么重，却藏着一个很朴素的愿望，想把生活重新放轻一点。许巍写了太多远方和理想，《简单》像是在说，真正难的也许不是走得多远，而是活得更干净一点。",
    "p2_jiuyue": "第二名，《九月》。它收在两千年的《那一年》里，同张有《故乡》《今夜》《那一年》这些更有大众记忆的作品，《九月》反而像藏在专辑中段的一阵风。《那一年》整张由许巍一个人包办词、曲、演唱和制作，能听见他那段最深的心事。而《九月》的好，就好在清冷、疏离、有季节感，像一个人在秋天里，慢慢回头看自己。",
    "p1_tianee": "第一名，《天鹅之旅》。它是二零零二年《时光·漫步》的开场第一首，可一开张，就被后面的《蓝莲花》《完美生活》《礼物》盖了过去。但它其实最能代表许巍的那次转身，从早期的沉郁，慢慢走向开阔：吉他明亮，鼓点有力量，情绪不再苦在低处，而是一点一点，朝着远方走。它不是最路人的那首许巍，却把旅途感和重生感，唱得最透。这，才是最被低估的许巍。",
    "outro": "五首歌盘完。第五，故事；第四，夏日的风；第三，简单；第二，九月；第一，天鹅之旅。许巍从来不只是那个唱远方和理想的摇滚诗人，他也很会在喧嚣落定之后，用最轻、最松弛的方式，把生活和心事，慢慢讲给你听。这些被大歌盖住的遗珠，刚好补全了他更安静、也更被低估的另一面。",
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
