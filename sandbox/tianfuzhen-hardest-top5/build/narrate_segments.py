#!/usr/bin/env python3
"""Generate female narration wavs for the Tian Fuzhen hardest top 5 video."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SPEED = 1.02
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "田馥甄的难唱，很多时候不是用一个高音就能解释。她难在冷静里有暗涌，轻声里有支撑，情绪已经很深，声音还不能散。今天这五首，不在开头公布完整榜单，我们从第五名往第一名听，看她的细腻到底难在哪里。",
    "p5_maodun": "第五名，《矛盾》。这首的难，不是单点爆发，而是在摇滚编曲里一直维持张力。主歌和副歌的情绪反差很大，高位推进时音准和咬字都不能松。唱太柔没有冲突，直接硬顶又会粗，真正难的是把矛盾感唱出来，还保留她声音里的清透和锋利。",
    "p4_xuanri": "第四名，《悬日》。它不是靠飙高音取胜，而是靠气息线和乐句完整度折磨人。旋律看似平缓，句子之间连接却很密，速度和情绪不能忽快忽慢。唱得太实会沉，唱得太虚会飘，最难的是轻轻唱，却不能散。",
    "p3_mogui": "第三名，《魔鬼中的天使》。这首难在高位爆发和音色控制。副歌要有力量、有穿透力，但不能变成大嗓门苦情歌；主歌又要保留轻声、气声和危险感。魔鬼和天使要同时存在，既锋利，又柔软，既爆发，又不能失控。",
    "p2_buyao": "第二名，《你就不要想起我》。它是典型的听起来会唱，真正唱很难稳。副歌一直往高位推，情绪越来越满，但声音不能变粗，不能喊散，尾音和长句还要撑住。最难的是那种逞强感，明明情绪快爆了，声音还要清亮、克制、精准。",
    "p1_fengci": "第一名，《讽刺的情书》。这是田馥甄后期作品里很硬的一首。难点不只是音域跨度，而是主歌和副歌速度感不同，字句又绵密。主歌要像女作家一样喃喃自语，副歌又要把情绪打开。唱轻了没张力，唱重了会失去那种细腻、冷静又隐痛的质感。",
    "outro": "最后总结这期排名。第五《矛盾》，第四《悬日》，第三《魔鬼中的天使》，第二《你就不要想起我》，第一《讽刺的情书》。田馥甄最难的地方，不只是唱到哪里，而是情绪已经抵达边缘，声音还要保持优雅、清醒和准确。",
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:12s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
