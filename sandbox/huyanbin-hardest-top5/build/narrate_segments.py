#!/usr/bin/env python3
"""Generate female narration wavs for 胡彦斌最难的5首歌."""
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
    "intro": "胡彦斌的歌，难点经常不是一句高音，而是一整首都在考你。节奏、咬字、转音、真假声、情绪和气口，全都得同时在线。这一期按难度从第五名倒数到第一名，先不剧透榜首，直接从最容易被低估的一首开始。",
    "p5_shiye": "第五名，《失业情歌》。它不是传统飙高音歌，难在叙事节奏和生活感。你要把接近说唱和念白的句子唱清楚，同时副歌又得撑出情绪。唱松了像流水账，唱太满又没了成年人被生活按住的苦味。",
    "p4_juebieshi": "第四名，《诀别诗》。这是影视主题曲式的难，旋律要撑得开，情绪要有诀别的重量，但不能从头硬喊。副歌如果气息不够，很容易从沙场诀别，唱成体测最后一圈。它考的是悲壮感和控制力。",
    "p3_hongyan": "第三名，《红颜》。这首难在中国风腔体和流行唱法的结合。它要有一点侠气、柔韧和古风线条，但又不能太刻意，不能唱成模仿戏腔。真正难的是：既要流行，又不能丢掉那股江湖感。",
    "p2_yueguang": "第二名，《月光》。它和《红颜》一样，是胡彦斌把中国风和流行融合的代表。但《月光》的难点不只是高，而是国风腔体、R and B 转音、假声控制和咬字稳定一起上。副歌要飘，又不能虚；转音要细，发声位置还不能乱。",
    "p1_quannazou": "第一名，《你要的全拿走》。这首我会放第一，因为它难的不是单纯高，而是密、长、急、绕。副歌歌词量大，节奏推进快，还要保持清晰咬字和讽刺感。唱慢一点没味道，唱急一点就糊，完整唱下来非常吃气息和节奏控制。",
    "outro": "最后回看这份榜单：第五，《失业情歌》；第四，《诀别诗》；第三，《红颜》；第二，《月光》；第一，《你要的全拿走》。胡彦斌真正难的地方，是他总把技术藏在歌曲表达里。你以为只是好听，其实每一句都在要稳定、要脑子、也要体力。",
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
