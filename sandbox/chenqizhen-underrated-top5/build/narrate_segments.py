#!/usr/bin/env python3
"""Generate female narration wavs for 陈绮贞最被低估的5首歌."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "很多人提到陈绮贞，第一时间会想到《旅行的意义》，想到《还是会寂寞》，想到那种清清淡淡的文艺感。可她真正厉害的地方，往往藏在那些没被大众反复讨论的歌里。这一期，我们只聊五首被低估的陈绮贞，从第五名开始，慢慢往第一名走。",
    "p5_juli": "第五名，《距离》。它在《Groupies 吉他手》时期显得很安静。同一张专辑里，大家更容易讨论《吉他手》和《小步舞曲》，可《距离》特别耐听。它没有很大的高潮，也没有故意制造爆点，更像一封永远寄不出去的信。听完以后，心里会有一点空。",
    "p4_taicongming": "第四名，《太聪明》。在歌迷圈里，这首的地位一直很高，但大众讨论度远远不如《旅行的意义》。它厉害的地方，是很早就把爱情里的自我觉察写出来了。二十岁听，可能只觉得好听；三十岁再听，很多句子会突然刺回来。",
    "p3_yigui": "第三名，《躺在你的衣柜》。这是真爱粉很爱的神曲，路人却很少知道。它的歌词像一个偷偷喜欢人的女生，在房间里自言自语。有点怪，有点可爱，也有点悲伤。那种带着幻想和别扭的少女感，后来在陈绮贞的歌里越来越少见。",
    "p2_wanmei80": "第二名，《百分之八十完美的日子》。很多人听过《太阳》，却不一定记得这一首。它有陈绮贞后期特别迷人的状态：不再只纠结爱情，而是开始观察生活。没有很大的情绪，却全是人生。属于十年前听觉得淡，十年后会越来越喜欢的作品。",
    "p1_fuxiu": "第一名，《腐朽》。这是我心里最被低估的一首。《华丽的冒险》里，《旅行的意义》《花的姿态》《华丽的冒险》都太耀眼，结果《腐朽》被埋在专辑里。可是很多老歌迷会告诉你，这首才是那张专辑里最陈绮贞的歌之一。它写时间、衰败和失去，冷静到残忍。越长大，越听得懂。",
    "outro": "所以陈绮贞被低估的歌，从来不只是冷门而已。它们更像是在热门歌曲旁边留下的暗线：少女感、生活感、距离感，还有对时间的清醒。她最动人的地方，常常不是把情绪说满，而是轻轻放在那里，等很多年以后，你自己听懂。",
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
