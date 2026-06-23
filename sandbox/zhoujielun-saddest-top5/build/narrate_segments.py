#!/usr/bin/env python3
"""Generate narration wavs for 周杰伦最苦的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序：05《世界末日》→ 04《不能说的秘密》→ 03《黑色毛衣》→ 02《轨迹》→ 01《搁浅》
BLOCKS = {
    "intro": "周杰伦的情歌，最狠的从来不是嘶吼。他越唱得轻，越像把最深的那道伤，悄悄藏进了旋律里。今天这五首，是周杰伦最苦的歌。",
    "p5_shijiemori": "第五名，《世界末日》。它苦的不是失恋本身，而是失去那个人之后，整个世界都像停了电。不是求你别走，而是我已经不知道，这个世界还剩下什么。",
    "p4_bunengshuo": "第四名，《不能说的秘密》。普通情歌唱的是我们不能在一起，这首唱的是，我明明知道你存在过，却没办法向全世界证明你存在过。那段爱，像被时间藏了起来，只剩他一个人还相信。",
    "p3_heiseimaoyi": "第三名，《黑色毛衣》。它没写机场，没写雨夜，只写了一件毛衣。分开以后，这件再普通不过的衣服，突然变成了证据，证明两个人曾经靠得很近，也证明现在，只剩一个人留在原地。",
    "p2_guiji": "第二名，《轨迹》。它苦在，人已经走了，可生活里到处都是他走过的痕迹。你以为自己已经走远，结果每一步，还是踩在那个人留下的轨迹上。",
    "p1_geqian": "第一名，《搁浅》。它必须排第一。最苦的不是分开，而是明明还爱，却已经回不到原点。前面压着懊悔，副歌一下，把那种想回去、却回不去的无力感全部推出来。这种苦，比被甩更狠，因为它带着自责。",
    "outro": "完整榜单。第五，《世界末日》。第四，《不能说的秘密》。第三，《黑色毛衣》。第二，《轨迹》。第一，《搁浅》。周杰伦最苦的歌，从来不靠哭腔，他只是把那句没说出口的对不起，轻轻唱给你听。",
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
