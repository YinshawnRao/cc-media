#!/usr/bin/env python3
"""Generate female narration wavs for the 动力火车 hardest top 5 video."""
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
    "intro": "动力火车的难，不只是飙高音、嗓门大。两个人的高音要咬合，和声要顶住，情绪一路压着往上冲，到后面还得拼体能。这五首，从第五名数到第一名，排名我们留到最后。",
    "p5_chule": "第五名，《除了爱你还能爱谁》。这首是张雨生写的，旋律线特别宽，老逼着人往上走。它不靠最炸，难在情绪浓、气息要稳。副歌想唱出那股深情，可声压和气息一不够，就卡在半空，上不去也下不来。",
    "p4_beipan": "第四名，《背叛情歌》。这首比听起来更耗。它不是一上来就炸，而是前面慢慢铺，张力一直绷着，到后面才整个爆开。最难的是从头到尾都不能松，情绪压满整首，唱到最后嗓子和气息一起被掏空。",
    "p3_wuqing": "第三名，《无情的情书》。这是他们出道的招牌难歌。爆发密度特别高，声音要厚、情绪要狠，可又不能只是吼。两个人一句接一句往上顶，气口很短，稍微一虚，那股狠劲就垮了。",
    "p2_caihong": "第二名，《彩虹》。这首难在副歌一整段都挂在高位，不是某一个高音点，而是要一直撑住。唱轻了没力量，唱重了又变成硬喊。更难的是，它要同时唱出悲壮、温柔和坚定，三种情绪压在同一条旋律里。",
    "p1_mingtian": "第一名，《明天的明天的明天》。这首几乎是动力火车难度的天花板。歌长将近七分钟，全程高压，双人和声要严丝合缝，到尾段还要拼体能。它不给你喘气的地方，越往后越要往上顶，普通人撑到副歌就没气了，他们却要一路稳到最后一个字。",
    "outro": "最后揭晓这一期的排名。第五，《除了爱你还能爱谁》；第四，《背叛情歌》；第三，《无情的情书》；第二，《彩虹》；第一，《明天的明天的明天》。动力火车的难，从来不是一个人能飙多高，而是两个人的力量、嘶吼和情绪，能不能在同一个高压点上，一起稳住。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（见 tools/video/outro_cta.py / CONVENTIONS「固定结尾配音」）。
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
        print(f"{key:12s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
