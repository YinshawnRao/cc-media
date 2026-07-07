#!/usr/bin/env python3
"""Generate narration wavs for 告五人最被低估的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序：05《爱在夏天》→ 04《夜里无星》→ 03《同样一个你》→ 02《带你飞》→ 01《你要不要吃哈密瓜》
BLOCKS = {
    "intro": "提到告五人，你先想到的，总是那几首大热门。可有些歌一样动人，却始终被忽略。今天这五首，是告五人最被低估的歌。",
    "p5_aizaixiatian": "第五名，《爱在夏天》。它没有特别强的传播点，却把夏天写得很干净。阳光、热气、喜欢的人，还有那些没说出口的心事，轻轻的，真真的，像一首被夏天藏起来的小歌。",
    "p4_yeliwuxing": "第四名，《夜里无星》。同一张专辑里，它被那几首大歌盖得最狠。它更暗，也更安静，像夜里没有星的时候，一个人把想说的话，全都收进了心里。",
    "p3_tongyang": "第三名，《同样一个你》。它不是第一耳朵的爆款，却越听越有味道。明明还是同一个人，可关系、距离、心境，早就都变了。告五人最擅长的，就是这种说不清的旧事。",
    "p2_dainifei": "第二名，《带你飞》。在同名专辑里，它的存在感反而没那么强。可它特别有告五人的团魂，轻快、明亮、一路向前，像有人拉你一把，带你去更远的地方。",
    "p1_hami": "第一名，《你要不要吃哈密瓜》。它必须排第一。歌名听着轻，情绪却又甜又真。不靠大副歌煽情，只用最生活、最可爱的口吻，把暧昧里的那点试探和靠近，唱成了夏天傍晚的一阵心动。",
    "outro": "完整榜单。第五，《爱在夏天》。第四，《夜里无星》。第三，《同样一个你》。第二，《带你飞》。第一，《你要不要吃哈密瓜》。告五人最迷人的地方，从来不在最红的那几首，而藏在这些被低估的角落里。",
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
