#!/usr/bin/env python3
"""Generate narration wavs for 陈粒最难唱的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序：05《桥豆麻袋》→ 04《小半》→ 03《光》→ 02《走马》→ 01《易燃易爆炸》
BLOCKS = {
    "intro": "陈粒的歌，听着随性，唱起来却全是坑。气息、咬字、真假声，还有情绪的收和放，每一样都在考验功底。今天这五首，是陈粒最难唱的歌。",
    "p5_qiaodou": "第五名，《桥豆麻袋》。名字听着像在闹着玩，唱起来却最容易翻车。它难在节奏和口语感，要俏皮，要一点暧昧，还要带点怪，可又不能真的唱成胡闹。咬字、停顿、律动、表情，差一点，味道就散了。陈粒最厉害的，是怪得特别自然。",
    "p4_xiaoban": "第四名，《小半》。这首很红，但是真的难。整首歌快五分钟，气息线特别长，副歌还要在压抑和爆发之间来回拿捏。它不是靠高音难，是靠情绪一直悬着难。主歌要淡，副歌要痛，可痛还不能俗。一旦用力过猛，那点欲言又止的小心事，就没了。",
    "p3_guang": "第三名，《光》。它藏在《如也》里，专辑里排第五，前面压着《奇妙能力歌》《历历万乡》这些更出名的歌，可《光》本身，最考验声音状态。它难在弱声和明亮度，声音要轻，但不能虚，情绪要亮，但不能甜。唱不好就发平，唱过头，又丢了那股清冷透明的劲儿。",
    "p2_zouma": "第二名，《走马》。听上去是一首很顺的民谣，真正难的，是叙事和气息。旋律不算夸张，可每一句都得有画面、有停顿、有递进。唱得太平，就像在念词，唱得太满，又没了走过一段旧事的那种轻。陈粒最绝的，是松弛里还藏着锋利，这两样，一般人很难同时拿住。",
    "p1_yiran": "第一名，《易燃易爆炸》。它必须排第一。难的不是某一个高音，是整首歌的情绪压强。前面要冷，要忍着，后面又要突然炸开，声音里得有危险感，可一旦炸成乱喊，就全废了。主歌低位的咬字要稳，副歌的爆发要有冲击，真假声的边缘，气息的控制，全是硬功夫。前面没气场，后面一炸就散。",
    "outro": "从《桥豆麻袋》到《易燃易爆炸》，陈粒最难唱的这五首，难的从来不是炫技。她把气息、咬字、收和放，全都藏进了那股随性里，听着轻松，唱起来要命。能把难，唱得像不费劲，才是真本事。",
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
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
