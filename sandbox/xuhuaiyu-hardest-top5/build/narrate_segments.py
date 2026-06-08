#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。
徐怀钰最难的5首歌 / 倒数 5→1（#1《飞起来》压轴）。
用户指定：开头、歌曲转场、结尾都要女性配音；片头不暴露歌曲排名。
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
SPEED = 1.04

BLOCKS = {
    "intro": "提到徐怀钰，很多人第一反应是青春、元气、甜美、洗脑。但她最难的歌，恰恰藏在这种轻快感里面。听起来越轻松，越要求气息、咬字、音色和节奏都稳住。今天这五首，不先剧透排名，我们从第五名开始。",
    "p5_miaomiao": "第五，《妙妙妙》。它表面是洗脑神曲，其实是节奏、气息和咬字的三重考验。旋律一直跳，歌词一直推，声音还要保持明亮、俏皮、有弹性。唱得太用力会笨，唱得太轻又没劲，最难的是让舞曲听起来很轻松，但身体其实一直在高速运转。",
    "p4_yihan": "第四，《心中的遗憾》。这首难在成熟声线和情绪厚度。它不像早期快歌那样靠速度制造压力，而是要在中高区持续推进情绪。声音要有力量，但不能粗；长句和尾音要稳住，情绪要厚，却不能压垮。对徐怀钰来说，这是从元气少女走向成熟表达的一首硬歌。",
    "p3_fenfei": "第三，《分飞》。这是她抒情歌里最考验稳定性的一首。副歌旋律线拉得很开，高位要稳，气息要长，情绪还要有破碎感，但声音不能真的散掉。它不是炫技型难歌，而是要在细腻、明亮和伤感之间保持平衡；唱重了会俗，唱轻了又撑不住。",
    "p2_callme": "第二，《Call Me》。这是典型的快歌高压型。旋律位置偏高，歌词密度大，副歌还要一直保持甜感和弹性，不能喊、不能塌、不能糊字。普通人唱这首，很容易前面还在可爱，后面直接变成电话打不通，气也接不上。",
    "p1_feilai": "第一，《飞起来》。这首是徐怀钰最容易被低估的难歌。它听起来青春、轻快、很明亮，但真正唱起来气口非常紧，前段就有长时间几乎不给喘息的连续咬字，还要保持音色亮、状态轻。难点不是飙高音，而是快、亮、密，还不能让人听见你喘。",
    "outro": "所以这份榜单，从第五《妙妙妙》、第四《心中的遗憾》、第三《分飞》、第二《Call Me》，到第一《飞起来》。徐怀钰的难，不只是高音，而是把快歌唱得轻，把情歌唱得稳，把元气唱得一点都不费力。你心里她最难的一首，是哪一首？",
}

pipeline = KPipeline(lang_code="z")
meta = {}
Path("audio").mkdir(exist_ok=True)
for key, text in BLOCKS.items():
    chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:12s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
