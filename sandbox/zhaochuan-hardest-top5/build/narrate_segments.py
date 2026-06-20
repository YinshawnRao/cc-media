#!/usr/bin/env python3
"""Generate female narration wavs for the Zhao Chuan (赵传) hardest top 5 video."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"   # 女声（brief 明确要求开头/转场/结尾女声）
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "赵传，铁汉柔情，一把粗粝又高亢的嗓子，是华语乐坛最有辨识度的声音之一。但今天，我们不聊他有多红，只聊一件事——他的歌，到底有多难唱。从第五名开始，一首一首往上数。",
    "p5_wochou": "第五名，《我很丑可是我很温柔》。它太有名了，名气反而盖过了它的难。副歌要炸得开，撕裂的高音里还得带着摇滚的颗粒感。可光有大嗓门还不够，你得一边唱出丑的自嘲，一边唱出温柔的脆弱，两种情绪同时成立，才是这首歌真正的门槛。",
    "p4_gaoliang": "第四名，《红高粱》。它不是标准的情歌唱法，而是民歌腔、摇滚嗓、长气口和粗粝的爆发，全都堆在一起。妹妹你大胆地往前走，这一嗓子要吼出土地的厚重，和野性的生命力。普通人一唱，很容易就变成单纯地用力喊，喊得出声音，却喊不出那份粗粝、辽阔和不管不顾的劲儿。",
    "p3_aiyao": "第三名，《爱要怎么说出口》，李宗盛的词曲。这首歌的旋律线拉得特别宽，副歌全是长句，对气息和胸腔的支撑是硬考验。对赵传这种粗粝的嗓子来说，难点从来不是能不能喊上去，而是喊上去之后，字头还要咬得清楚，气不能散，情绪不能垮。一句没撑住，整段的力量就泄了。",
    "p2_gei": "第二名，《给所有知道我名字的人》，李宗盛作词，刘天健作曲。它最狠的地方，是越唱越高、越唱越重，一路都不能塌。这不是某一个高音的事，而是要把感恩、沧桑和倔强，一层一层往上推，一直推到结尾。尾段一旦撑不住，前面攒了整首的情绪，会在最后一句直接垮掉。",
    "p1_xiaoniao": "第一名，《我是一只小小鸟》。这首歌，让赵传站上了金曲奖最佳国语男歌手的领奖台。它排第一，不是因为最红，而是因为它把所有难度都压在了副歌——持续的高位、爆发的情绪、巨大的声压，一句叠着一句，没有喘息。我是一只小小鸟，想要飞却怎么样也飞不高，唱的是卑微，拼的却是真功夫。能把这份不甘唱得又高又不破，才真的明白，赵传有多强。",
    "outro": "再回顾一次这份榜单：第五，《我很丑可是我很温柔》；第四，《红高粱》；第三，《爱要怎么说出口》；第二，《给所有知道我名字的人》；第一，《我是一只小小鸟》。赵传的难，从来不是炫技的高音，而是他能把粗粝和温柔、卑微和倔强，同时塞进一把嗓子里，让每一个平凡人，都能在他的歌里，听见自己。",
    "outro_cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
