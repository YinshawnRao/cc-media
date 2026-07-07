#!/usr/bin/env python3
"""Male narration for 南拳妈妈最被低估的5首歌.

Countdown 5 -> 1 (#1 = 消失, the climax). 倒数揭晓。
事实口径（已核实，配音不得出错；详见 SOURCES.md）：
- 这 5 首全部出自南拳妈妈「第二代」四人时期（弹头/宇豪/Lara 梁心颐/AJ 张杰）。
- 离家不远 = 《调色盘》(2006) 末轨（第12首），词 宋健彰(弹头) / 曲 张杰；写给家人的情歌，Lara 的英文词写给姐姐。
- 最后一枚笑容 = 《2号餐》(2005)，词曲 宋健彰(弹头)，弹头 + Lara 同唱。
- 人鱼的眼泪 = 《调色盘》(2006)，词 黄俊郎 / 曲 巨炮 → 不能说"南拳妈妈自己写的"。
- 破晓 = 《2号餐》(2005) 开场曲，词 弹头 / 曲 宇豪，电子摇滚融合古典 + 24人爱乐弦乐，前奏近一分半，励志词。
- 消失 = 《2号餐》(2005)，词 弹头 / 曲 宇豪，周杰伦力挺主打；灵感是一个人失意游荡英国街头，编曲加车声/教堂钟声 + 24人弦乐。
英文/专辑外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
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
    "intro": "提到南拳妈妈，很多人第一时间想到的，是《牡丹江》《橘子汽水》，是那个夏天，几个大男孩加一个女声，把青春唱得又甜又燃。可在这些大热歌之外，他们还藏着不少更安静、更细腻的好歌，被一张张专辑的主打盖了过去。今天这期，我们就从第五名倒数，盘一盘南拳妈妈最被低估的五首歌。",
    "p5_lijia": "第五名，《离家不远》。它压在《调色盘》的最后一首，很容易在专辑快放完的时候被错过。可这首歌，是南拳妈妈四个人都很偏爱的一首：弹头的词，写尽了游子在外漂泊、想家的心情；Lara那段英文，是写给从小一起长大的姐姐。离家不远，可人已经开始往外走，那个家，被慢慢留在了身后。追梦飞累了，最暖的窝，终究还是自己的家。",
    "p4_xiaorong": "第四名，《最后一枚笑容》。它和《消失》《破晓》一样，收在二零零五年的《2号餐》里，可它没有《牡丹江》的中国风，也没有《橘子汽水》的校园甜味。这首歌词曲都是弹头一个人包办，由他和Lara一起唱。歌名就很有故事感：最后一枚笑容，像一段关系散场之前，留下的最后一点温柔。它不哭也不闹，只是带着一点克制、一点遗憾，和青春散场之后那种淡淡的空。",
    "p3_renyu": "第三名，《人鱼的眼泪》。它来自二零零六年的《调色盘》，同张专辑里，《初恋粉色系》《花恋蝶》更容易被记住，它就显得低调很多。这首歌的词，是周杰伦的老搭档黄俊郎写的，气质很特别：不是普通的伤感，而是带着一点童话、一点海水，和一种说不出口的遗憾。南拳妈妈常给人青春、明亮的一面，而这一首，更像藏在专辑深处的一条蓝色暗线。",
    "p2_poxiao": "第二名，《破晓》。它是《2号餐》的开场曲，可大众的记忆，几乎都被后面的《牡丹江》《橘子汽水》带走了。它把电子摇滚揉进古典弦乐，光是前奏，就铺了将近一分半。弹头写的词很燃：我不知道我会不会赢，但我不怕失败。它不是纯粹的甜，也不是纯粹的伤，而像天快亮之前的那一点光，听着听着，就有一种少年往前冲的画面。",
    "p1_xiaoshi": "第一名，《消失》。同样收在《2号餐》里，当年还被周杰伦特别看好。宇豪说，写这首歌的灵感，是想象一个人失意地，游荡在英国的街头，编曲里特意加进了车声和教堂的钟声，再铺上二十四人的弦乐团。它没有激烈的爆点，唱的是一段感情慢慢淡出、一个人慢慢离开的过程。感情像地平线一样无限延伸，辽阔，却孤独。这，才是最被低估的南拳妈妈。",
    "outro": "五首歌盘完。第五，离家不远；第四，最后一枚笑容；第三，人鱼的眼泪；第二，破晓；第一，消失。南拳妈妈从来不只是那个把夏天唱得又甜又燃的组合，他们也很会用最安静的方式，去写离别、写想家、写一个人慢慢消失的孤独。这些被大热歌盖住的遗珠，刚好补全了他们最细腻、也最被低估的另一面。",
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
