#!/usr/bin/env python3
"""Generate female narration wavs for the Xu Jiaying hardest top 5 video."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "徐佳莹的难唱，常常不是那种一眼就看出来的飙高音。她更难的地方，是强混、弱混、咬字、气息、风格切换和情绪控制同时发生。今天这五首，不先公布完整排名，我们从第五名开始，一首一首听她到底难在哪里。",
    "p5_daoci": "第五名，《到此为止》。这首旋律看起来不花哨，但副歌一直卡在很吃力的位置，咬字又密，情绪还要往前冲。真正难的是那种决绝感不能靠喊，声音要稳，气息要顶住，才有忍到尽头的重量。",
    "p4_huise": "第四名，《灰色》。难点在成熟阶段的声音控制。它不是外放式爆发，而是在更暗、更厚、更克制的音色里维持支撑。副歌情绪压得很深，唱太满会钝，唱太轻又撑不起灰色的重量。",
    "p3_shalu": "第三名，《失落沙洲》。它听起来安静，其实非常考验弱混、气息和音准。主歌要轻、要空，副歌又要慢慢推上去，但不能突然变重。最难的是透明感，不能虚，不能飘，也不能白。",
    "p2_baima": "第二名，《身骑白马》。它难在国语流行段落和台语歌仔戏段落之间的切换。不是单纯唱高，而是叙事感、腔体、音色、气息和情绪爆发一起变。普通人很容易唱成，身骑白马，气息落马。",
    "p1_jixian": "第一名，《极限》。这首是徐佳莹声乐难度里很容易被低估的一首。它不是传统大歌的高音炫技，而是在电子摇滚的压迫感里持续高位推进。声音要有爆发，但不能喊散；太轻没冲击，太重又失去她那种灵巧又神经质的边缘感。",
    "outro": "最后总结这期排名。第五《到此为止》，第四《灰色》，第三《失落沙洲》，第二《身骑白马》，第一《极限》。徐佳莹最难的地方，不只是唱得高，而是把技术藏在情绪里，还让每个字都稳稳落下。",
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
        print(f"{key:10s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
