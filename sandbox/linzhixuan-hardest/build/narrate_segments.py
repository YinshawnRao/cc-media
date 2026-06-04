#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。
林志炫最难的5首歌 / 倒数 5→1（#1《没离开过》压轴）。用户给定排名：
1 没离开过 / 2 如果不是因为你 / 3 散了吧 / 4 离人 / 5 认错。
用户指定：开头/转场/结尾女性配音 → 全程女声。
TTS 安全：不含英文字母/音名(G4/D5)，难度用中文描述；歌名英文/年份在字幕里给。
片头不剧透排名(仅封面+作品描述)，片尾完整榜单回顾。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到林志炫，你会想到那把干净、透明、稳得吓人的嗓音，觉得他唱高音好像毫不费力。可只要你自己张口就知道，这些歌，没有一首是好惹的。今天这五首，公认是林志炫最难唱的歌。我们从第五名开始。",
    "p5_rencuo": "第五，《认错》。这是他很早期的作品，难，就难在一个字，干净。它不像后面几首那样把人往死里压，可越是这种歌，越藏不住毛病。虚实之间要转得不留痕迹，音色从头到尾要统一，气息得连成一条细细的线。唱重了会土，唱虚了会飘，还得像他那样，声音很薄，却一点都不弱。",
    "p4_liren": "第四，《离人》。它难，不是难在吼。整首要在很高的位置上，保持一种透明、克制的音色，靠的是轻、是准、是稳。假声、弱混、真声之间，不能有半点断层和换挡的痕迹，情绪还要一路绷着不松。声音越往高处走，越要收着唱，这种高位置上的轻，最考验真功夫。",
    "p3_sanleba": "第三，《散了吧》。这首不是靠红上的榜，它是折磨型的难。被很多人称作著名的高音折磨曲，副歌一句接一句全顶在高位，到最后那一段，更是密集的高音连发。它折磨的地方在于，不是飙一下就完事，而是要在那么高的位置反复咬字、把情绪一层层往上推，气息和声带的闭合，从头到尾一点都不能松。",
    "p2_rgbsywn": "第二，《如果不是因为你》。它不算他最红的歌，可从声乐的角度看，硬得吓人。一整段连续的中高音咬字，每个字都要靠强混声稳稳撑住，音准的稳定性，要求高到离谱，里面还藏着他作品里数一数二的极限高音。这种歌，唱准一句不难，难的是从头到尾，没有一个字能塌下去。",
    "p1_mlkg": "第一，《没离开过》。说它是林志炫最难，几乎没人会反对。整首歌，长时间压在男声最难受的中高混声区，几乎从头到尾都不让你下来。副歌是大线条、大动态，渐弱、渐强、强弱之间的转换密得吓人，共鸣的位置还要不停地切换。它不是难一句，是难一整首，这，就是公认的，整首都泡在混声区的，变态级唱功。",
    "outro": "所以你看，林志炫那把听起来毫不费力的嗓子背后，是把最难的技术，唱成了云淡风轻。第五，《认错》；第四，《离人》；第三，《散了吧》；第二，《如果不是因为你》；第一，《没离开过》。这五首里，你心里林志炫最难的一首，是哪一首？评论区聊聊。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:12s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
