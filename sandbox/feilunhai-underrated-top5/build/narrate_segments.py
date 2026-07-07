#!/usr/bin/env python3
"""Generate narration wavs for 飞轮海最被低估的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序：05《最佳听众》→ 04《心里有数》→ 03《留下来》→ 02《夏雪》→ 01《一个人流浪》
BLOCKS = {
    "intro": "提起飞轮海，你大概会先想到那几首主打歌。可他们最温柔的那一面，常常被压在专辑里，没被好好听见。今天这五首，是飞轮海最被低估的歌。",
    "p5_zuijiatingzhong": "第五名，《最佳听众》，收录在《越来越爱》。比起《默默》和《孤单摩天轮》，它几乎没什么存在感。可它写的，不是站在爱情中心的那个人，而是一直在旁边、安静听你说话、默默陪着你的那一个。飞轮海的歌大多是青春和明亮，这一首，补上了他们很温柔的一面。",
    "p4_xinliyoushu": "第四名，《心里有数》，来自《双面飞轮海》。比起《新窝》《为你存在》这些更有主打感的歌，它低调得多。可它特别适合老粉重听。光是歌名，就藏着一种关系里的清醒：很多话没有说破，其实两个人心里都明白。这是飞轮海更内敛、也更成熟的一首情歌。",
    "p3_liuxialai": "第三名，《留下来》，同样收在《越来越爱》。它由五月天的怪兽作曲，却被专辑里的主打盖了过去，像藏在后半段的一颗遗珠。它不是一听就炸的歌，而是一种想挽留、又说得很克制的情绪。这是飞轮海情歌里，更成熟的那一面。",
    "p2_xiaxue": "第二名，《夏雪》，来自飞轮海的首张同名专辑。旋律很清新，情绪却一点都不轻。光是歌名就很有画面：明明是夏天，心里却下着雪；明明寒冬已经走远，回忆却迟迟没有融化。它不是最炸、也不是最甜的飞轮海，而是早期作品里，最容易被忽略的一首干净抒情歌。",
    "p1_yigerenliulang": "第一名，《一个人流浪》，同样来自首张同名专辑。在那些更好记的主打中间，它太容易被盖过去。可它恰恰代表了飞轮海，在偶像团体之外的那一面：不是热血少年，也不是甜甜的对唱，而是一个人离开以后，慢慢消化孤单。旋律不算最爆，却最耐听。这，就是我心里，飞轮海最被低估的一首歌。",
    "outro": "从《最佳听众》到《一个人流浪》，这五首，没有一首是当年的主打。可偏偏是这些被盖过的歌，藏着飞轮海最安静、也最深的那一面。偶像会长大，喧闹会过去，有些温柔，要等很多年以后，你才真的听懂。",
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
        print(f"{key:20s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
