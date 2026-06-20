#!/usr/bin/env python3
"""Generate Chinese narration wavs for 世界杯最佳主题曲 TOP5.

Song names are mostly visual-only per brief. Narration calls rank + World Cup year
and keeps the full-volume song showcases uninterrupted.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "如果世界杯主题曲只能选五首，我会更看重三件事：能不能代表主办地，能不能让全世界跟着唱，离开那届世界杯之后，还能不能被人记住。这期从第五名倒数到第一名。",
    "p5_time": "第五名，二零零六年德国世界杯。这一首不像看台上的口号，更像决赛之后的颁奖灯光。歌剧流行和节奏蓝调声线叠在一起，庄重、完整，也让那个夏天多了一点史诗感。",
    "p4_one": "第四名，二零一四年巴西世界杯。它的巴西本土感不算最满，但定位非常清楚：把开幕式变成全世界的派对。明星阵容、鼓点和口号，负责先把气氛点起来。",
    "p3_estate": "第三名，一九九零年意大利世界杯。老派世界杯的浪漫天花板。它不靠互联网传播，也不靠舞蹈梗，而是靠一种意大利之夏的辽阔感，把足球唱成了回忆。",
    "p2_copa": "第二名，一九九八年法国世界杯。真正把现代世界杯主题曲模板打出来的一首：拉丁节奏、桑巴律动、全场可以一起喊的口号，直接把舞台推到世界中心。",
    "p1_waka": "第一名，二零一零年南非世界杯。综合第一基本没悬念。主办地气质、全球传播、现场感染力、可跟唱程度全在线；这就是世界杯主题曲该有的样子。",
    "outro": "五首歌放在一起看，世界杯主题曲最难的地方，不只是好听，而是让不同语言的人，在同一瞬间跟上同一个节奏。能做到这一点的，才真的配得上那个夏天。",
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
