#!/usr/bin/env python3
"""Female narration for 王心凌最甜的5首歌.

Countdown playback order is 5 -> 1:
爱的套餐, 彩虹的微笑, 睫毛弯弯, 爱你, Honey.

The final CTA is imported from tools/video/outro_cta.py and remains the last
spoken line in the finished video.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
sys.path.insert(0, str(ROOT.parents[1] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": (
        "说到王心凌，很多人的第一反应是甜。"
        "但她厉害的地方，是把甜唱出了不同层次。"
        "今天从第五名倒数，盘一盘王心凌最甜的五首歌。"
        "最后那一首，基本就是甜心教主的招牌答案。"
    ),
    "p5_taocan": (
        "第五名，《爱的套餐》。这首歌像一份恋爱甜点菜单。"
        "节奏轻快，表情可爱，甜度不靠大嗓门，而是靠一句一句的小心思堆起来。"
    ),
    "p4_rainbow": (
        "第四名，《彩虹的微笑》。偶像剧的阳光感一出来，整个画面就亮了。"
        "它的甜是很明朗的，像雨后放晴，连烦恼都被笑容冲淡。"
    ),
    "p3_jiewanwan": (
        "第三名，《睫毛弯弯》。这首歌最可爱的地方，是它把眨眼、舞步和小女生的俏皮感都唱出来了。"
        "不是腻人的甜，是灵动又会撒娇的甜。"
    ),
    "p2_aini": (
        "第二名，《爱你》。它一响起，就是很多人对校园告白和甜心舞步的集体记忆。"
        "副歌够直接，动作够标志，甜得很有年代感，也很难被替代。"
    ),
    "p1_honey": (
        "第一名，《Honey》。压轴必须是它。"
        "这首歌几乎把王心凌的招牌甜度全部浓缩在一起：轻快、明亮、黏人，但又很有辨识度。"
        "说它是甜心教主的代表答案，一点都不过分。"
    ),
    "outro": (
        "五首歌盘完。第五，爱的套餐；第四，彩虹的微笑；第三，睫毛弯弯；"
        "第二，爱你；第一，Honey。"
        "王心凌的甜，不只是可爱，而是一种能把青春记忆重新点亮的声音。"
    ),
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
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
