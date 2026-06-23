#!/usr/bin/env python3
"""Generate narration wavs for 张信哲最苦的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "张信哲最苦的歌，不是把伤口撕开给你看。他越是唱得轻，越像一个人已经把所有委屈咽下去了。今天这五首，不先摊开答案，从第五名往第一名数。",
    "p5_xinyang": "第五名，《信仰》。这首的苦不在分手现场，而在把爱情唱成一种信仰。听起来很干净，可一旦爱变得神圣，失去也会变得特别残忍。",
    "p4_yongqing": "第四名，《用情》。它像一个人反复告诉自己已经没事，结果越想忘，越证明还在乎。不争，不闹，不追问，只是在时间里承认，真正用过情的人，没那么容易全身而退。",
    "p3_biepawoshangxin": "第三名，《别怕我伤心》。最苦的地方，其实就在歌名里。不是我不伤心，是我怕我的伤心也变成你的负担。成年人听到这里，很难不突然安静一下。",
    "p2_airuchaoshui": "第二名，《爱如潮水》。它不是简单的我失去你，而是我明知道你未必属于我，还是想替你挡住所有危险。爱像潮水推过去，最后先被淹没的，可能就是自己。",
    "p1_guohuo": "第一名，《过火》。这首必须压轴，因为它不是普通失恋。明明被伤得很深，他还在替对方找理由，甚至把责任往自己身上揽。张信哲最可怕的地方就是，他不吼，听的人反而更难受。",
    "outro": "完整榜单揭晓。第五，《信仰》。第四，《用情》。第三，《别怕我伤心》。第二，《爱如潮水》。第一，《过火》。张信哲最苦的歌，苦在没有怨气，苦在明明已经很痛，还要把爱唱得体面又干净。",
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
