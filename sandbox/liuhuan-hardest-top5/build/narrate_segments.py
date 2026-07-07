#!/usr/bin/env python3
"""Generate narration wavs for 刘欢最难的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
GUARD_PREFIX = "接下来，"

BLOCKS = {
    "intro": "刘欢的难，从来不只是音高。是气息、咬字、厚度、戏剧感和时代气场一起压上来。今天这五首，按难度倒着揭晓，越往后，越能听出他的分量。",
    "p5_congtou": "第五名，《从头再来》。它不是最高最炸，却很难唱出真正的重量。情绪必须真，句子要直，不能油，也不能像喊口号。它难在经历低谷之后，声音还要稳稳站起来。唱轻了没有力量，唱太煽情又容易俗。",
    "p4_haohange": "第四名，《好汉歌》。这首太红，所以难度常被低估。它要的不是精致，而是豪气、粗粝、开阔和民间性。声音要厚，咬字要硬，气口还要稳。唱轻了没有江湖气，唱重了又会变成吼。",
    "p3_qianwan": "第三名，《千万次的问》。它难在持续高位和情绪推进，不是一个点高，而是整首都要有追问感。主歌要有悬念，副歌要爆发，声音还不能散。真正难的，是有力量，同时还有层次。",
    "p2_wanwan": "第二名，《弯弯的月亮》。它听起来温柔，其实非常难唱好。长句气息、弱声控制、情绪留白，一个都不能掉。唱得太满，乡愁会变苦情；唱得太轻，又撑不起那种穿过时间的忧伤。",
    "p1_fenghuang": "第一名，《凤凰于飞》。它必须放第一。它不是单纯高音难，而是古典审美、长线条气息和戏剧张力一起难。咬字不能太现代，气息要稳住缓慢铺开的旋律。唱轻了没格局，唱重了又失去古风的飘逸和贵气。",
    "outro": "完整榜单。第五，《从头再来》。第四，《好汉歌》。第三，《千万次的问》。第二，《弯弯的月亮》。第一，《凤凰于飞》。刘欢最难的地方，是他总能把厚重唱得不笨，把豪迈唱得有根，把戏剧感唱得像命运本身。",
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
}


def synth_text(key: str, text: str) -> str:
    # Kokoro sometimes drops the first phrase of a long isolated Chinese segment.
    if key.startswith("p") or key == "outro":
        return GUARD_PREFIX + text
    return text


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        spoken = synth_text(key, text)
        chunks = [audio for _, _, audio in pipeline(spoken, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {
            "text": text,
            "spoken_text": spoken,
            "dur": round(len(audio) / SR, 3),
            "voice": VOICE,
        }
        print(f"{key:20s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
