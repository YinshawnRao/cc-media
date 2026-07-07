#!/usr/bin/env python3
"""Generate narration wavs for 罗志祥最难的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序（倒数）：05《不具名的悲伤》→ 04《拼什么》→ 03《独一无二》→ 02《舞极限》→ 01《精舞门》
# 事实硬约束：① 五首没有一首是罗志祥本人作曲作词，旁白不得说"他写的"；
#            ② 《精舞门》是2006《Speshow》主打，与2008同名电影无关，不提电影。
BLOCKS = {
    "intro": "提到罗志祥，你先想到的多半是亚洲舞王，是那身停不下来的舞步。可他的歌真正难的地方，从来不只是跳。是跳到快缺氧，声音还得稳稳在线。今天这五首，是罗志祥最难的五首歌。",
    "p5_bujuming": "第五名，《不具名的悲伤》。这是一首五分多钟的慢歌，难在耐力。它不是一上来就哭，而是把一种说不出名字的悲伤，一点一点往上堆。主歌要收着唱，副歌要撑得住，到了尾段，气息和情绪都不能塌。罗志祥很多快歌难在唱跳，这一首，难在站着唱，也糊弄不过去。",
    "p4_pinshenme": "第四名，《拼什么》。《独一无二》那张专辑，他难得地把一首慢歌，放上了第一主打。难点不在跳，而在情绪和唱功。前面要稳、要真，后面要爆发，又不能唱成硬挤。情绪不够会发平，情绪太满又容易失控。据说为了这首歌，他在镜头前一遍遍重来，唱到自己先红了眼眶。",
    "p3_duyiwuer": "第三名，《独一无二》。同名专辑的主打，用电子曲风，把那句独一无二的个性宣言顶到最前面。它难在电子舞曲里的节奏控制和声音稳定。要有态度、有律动、咬字还要清楚，更关键的是，声音不能被一层层编曲吞掉。舞曲最怕声音发虚，一虚，就只剩伴奏在卖力。",
    "p2_wujixian": "第二名，《舞极限》。这是一首唱跳高压型的作品，难点在持续的律动和现场体能。它不是站着唱准就完事，而是从头到尾，身体的节奏、声音的稳定、舞台的爆发力，得一直顶着。副歌要炸，但不能喊散，节奏要紧，但不能赶拍。它考的不是单一唱功，是一个舞台歌手的完整能力。",
    "p1_jingwumen": "第一名，《精舞门》。它必须排第一。这首不靠高音取胜，靠的是唱、跳、节奏、体能同时在线的综合难度。节奏密、字多、气口短，还得配着高强度的舞蹈动作。副歌要有冲击力，说唱段要咬字清楚，整首还得撑住舞台气势。普通人唱这首最尴尬的，是跳起来气不够，不跳又没了灵魂。能把它完整拿下来的，真没几个。",
    "outro": "五首盘下来你会发现，罗志祥的难，是两种难。快歌难在唱跳和体能同时拉满，慢歌难在站着唱也不能糊弄。我们总记得那个跳到发光的舞王，却容易忘了，撑起这些舞台的，是真功夫。",
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
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
