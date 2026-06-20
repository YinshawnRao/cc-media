#!/usr/bin/env python3
"""Female narration for 童安格最被低估的5首歌.

Countdown order is 5 -> 1. The final CTA is imported from tools/video/outro_cta.py
because it is a repo-level convention.
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
    "intro": "说到童安格，很多人会先想起《其实你不懂我的心》《明天你是否依然爱我》，或者《把根留住》。但童安格真正迷人的地方，不只在这些大歌里。今天这期，我们从第五名倒数，聊五首更安静、更耐听，也更容易被低估的童安格遗珠。",
    "p5_lamp": "第五名，《整个世界只留下一盏灯》。这首放在收尾气质里很特别，歌名本身就像一幅电影画面：世界都暗下来了，只剩一盏灯还在等人回来。它没有全民记忆点，但氛围非常强，童安格用很轻的声音，唱出很深的孤独。",
    "p4_water": "第四名，《水中的颜》。这首冷门感很够，也很有早期童安格的文艺气质。歌名像一张被水波晃动的旧照片，旋律不走大众金曲路线，却能听见他那种干净、忧郁、带一点诗意的表达。",
    "p3_dawn": "第三名，《陪你到天亮》。它不是那种一开口就抓人的大热歌，而是越夜越好听的陪伴型情歌。不是承诺永远，只是陪你到天亮。温柔，但不是甜；安静，却很有重量。",
    "p2_dream": "第二名，《等我一起入梦》。这首很适合放在前面的位置，因为它有很完整的梦境感和陪伴感。像一个人在夜里轻轻说，别一个人寂寞，等我一起入梦。它不是爆款旋律，却特别有童安格式的温柔、孤独和诗意。",
    "p1_passby": "第一名，《你我的爱只能擦肩而过》。这首我还是放第一。它不是童安格最路人化的金曲，却非常能代表他那种文雅、克制、旧时代情歌里的遗憾感。不是大哭大闹的失恋，而是明明爱过，却只能在命运里错身而过。",
    "outro": "所以童安格最迷人的地方，也许从来不是把情绪唱得很满，而是轻轻放在那里，让后劲慢慢回来。从第五到第一，这五首歌都不喧哗，却很耐听。它们像夜里的一盏灯，也像水面上一点慢慢散开的波纹。",
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
        print(f"{key:15s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
