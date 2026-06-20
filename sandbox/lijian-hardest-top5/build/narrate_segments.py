#!/usr/bin/env python3
"""Generate female narration wavs for the Li Jian hardest top 5 video."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SPEED = 1.02
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "李健最难的歌，难点往往不是炸，而是轻、稳、长、准。普通人唱李健，最容易把高级感唱成用力感。这期按你给的排名，从第五名往第一名听。",
    "p5_meiruo": "第五名，《美若黎明》。它难在明亮但不能刺，轻盈但不能飘。整首歌像清晨第一束光，声音要打开，却不能用蛮力；唱得太实会笨，唱得太虚又会塌。",
    "p4_chuanqi": "第四名，《传奇》。它太红了，所以很多人低估它的难。旋律干净到没有地方躲，气息、音准、尾音、咬字稍微脏一点都会被听出来。唱这首，不是拼嗓门，是拼一根线能不能拉得又细又稳。",
    "p3_xiangwang": "第三名，《向往》。这首不是只负责好听，它真正考的是干净、舒展和明亮感。声音不能太满，也不能太软，要像风一样往前走，但脚下还得很稳。",
    "p2_tianyi": "第二名，《假如爱有天意》。它最难的是情绪递进。前面要轻、要远，后面要开、要撑，不能一开始就用满力；控制不住，副歌就会从宿命感变成努力感。",
    "p1_baikal": "第一名，《贝加尔湖畔》。这首难点不是炸，而是轻。旋律线很长，气息要稳，声音还要一直空灵、流动，尤其高位弱声，唱轻了虚，唱重了俗。普通人一开口，容易把贝加尔湖唱成小区人工湖。",
    "outro": "最后总结。第五《美若黎明》，第四《传奇》，第三《向往》，第二《假如爱有天意》，第一《贝加尔湖畔》。李健的难，是你明明听见它很轻，真唱才发现每一口气、每一个尾音都要撑住。",
    # Fixed series CTA. Must remain the last spoken sentence.
    "outro_cta": FIXED_OUTRO_CTA,
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
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
