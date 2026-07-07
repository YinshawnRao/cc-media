#!/usr/bin/env python3
"""Generate narration wavs for 杨丞琳最被低估的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序（倒数）：05《怕》→ 04《鱼鳃》→ 03《折叠式爱情》→ 02《自作自受》→ 01《冷战》
BLOCKS = {
    "intro": "提到杨丞琳，你会想起那些甜的、那些酷的。可她真正被低估的，是把爱情里的不安和退缩，唱得很轻的那一面。今天这五首，是我心里，杨丞琳最被低估的歌。",
    "p5_pa": "第五名，《怕》。它没有大起大落，唱的是爱情里最本能的那点反应——怕失去，怕受伤，怕刚靠近，又被推开。她把这种不安全感，唱得很轻，轻到你以为没事，可它最扎心。",
    "p4_yusai": "第四名，《鱼鳃》。鱼要有鳃才能呼吸，人也一样，得抓住某一段关系、某一点理解，才能在爱里活下去。它不是寻常的苦情歌，而是把那种快要窒息、却还在自我保护的状态，藏进了海一样的旋律里。",
    "p3_zhediee": "第三名，《折叠式爱情》。爱情在这首歌里，是可以被折叠、被收起来的——被抱在怀里，却还要提防对方；明明像是幸福，又夹着一点伤。姚若龙的词，把那种困在假象里的敏感和不安，写得特别具体。",
    "p2_zizuozishou": "第二名，《自作自受》。明明已经受了伤，却还在一遍遍替对方找理由，最后只能承认，这一切都是自作自受。从不甘，到崩溃，再到看清自己的执念，她唱出了一整段情绪的塌方。",
    "p1_lengzhan": "第一名，《冷战》。它必须排第一。它没把僵持写成大吵大闹，而是写成两个人都不说、都不退、都在等对方先低头的消耗。她唱得压抑、克制，把成年人爱情里最难熬的那种沉默，闷在了整首歌里。",
    "outro": "第五，《怕》；第四，《鱼鳃》；第三，《折叠式爱情》；第二，《自作自受》；第一，《冷战》。杨丞琳被低估的，从来不是唱功，而是她愿意把爱情里最不体面、最退缩的那一部分，唱得这么轻，又这么真。",
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
