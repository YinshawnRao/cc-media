#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。
梁博最难的5首歌 / 倒数 5→1（#1 灵魂歌手 压轴）。
用户指定：开头/转场/结尾女性配音 → 全程女声。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到梁博，很多人第一反应是：太稳，太松弛，好像根本没在用力。可正是这种毫不费力的错觉，藏着华语乐坛最难复刻的一种唱法。今天这五首，是公认梁博最难唱的歌。难，不在飙多高的音，而在他怎么把强混、撕裂和长线的高压，唱得像呼吸一样自然。我们从第五名开始。",
    "p5_nanhai": "第五，《男孩》。它的技术难度也许不是梁博最顶的，但放进这份榜单，一点都不亏。副歌一直在换声区附近反复顶，既要有少年气，又不能唱薄、唱虚。最麻烦的是，这首歌太多人会唱了，稍微唱白、唱油，一秒就被听出来。越是大家都熟的歌，越藏不住功力。",
    "p4_chuxian": "第四，《出现又离开》。这首特别容易被低估。它不靠炸取胜，难点全在长气息、真假声，还有轻重声之间的转换，以及那种一直悬着、迟迟不肯落地的遗憾感。唱得太满就俗了，唱得太轻，又撑不起副歌。要把克制和深情卡在同一条线上，比飙高音难多了。",
    "p3_heiye": "第三，《黑夜中》。复古摇滚的律动，难就难在又松又狠。节奏要稳，律动要准，声音还得带着粗粝的颗粒感和穿透力。唱得太正，味儿就没了；唱得太野，又容易跑音、挤嗓子。要在松弛和爆发之间反复横跳，还不能掉拍，这是另一种硬功夫。",
    "p2_biaotai": "第二，《表态》。如果要选一首代表梁博其实很难唱，就是它。它不是炫技型的难，而是一路往前推：情绪、节奏、咬字、胸声的厚度，一个都不能塌。气口极少，副歌要是只会喊，立刻就糊。要顶着这么强的压迫感往前冲，还得字字清楚，太考验底子了。",
    "p1_lhgs": "第一，《灵魂歌手》。说梁博最难，放这首没人会有意见。它难的不是某一个高音，而是整首歌的持续输出：沙哑的颗粒、密不透风的强混、一层层往上爆发的情绪，还要在乐队的声压里，让人声始终穿透出来。全程都要顶住，一秒都不能松。这不是炫技，这是把嗓子当成乐器，硬扛到底。",
    "outro": "所以梁博从来不是唱得轻松，而是把最难的东西，唱成了听起来毫不费力。强混、撕裂、长线高压，他全都收进了那一份稳里。这五首，你心里梁博最难的一首，是哪一首？评论区告诉我。",
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
