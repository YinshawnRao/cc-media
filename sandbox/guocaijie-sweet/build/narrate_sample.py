#!/usr/bin/env python3
"""样片旁白：女声 zf_xiaoyi。开头钩子 + 过桥 + No.1 Little Sunshine voice + 金句。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"   # 女声（brief 指定女性配音）
SR = 24000
SPEED = 1.03          # 甜妹轻快

BLOCKS = {
    "intro": "很多人认识郭采洁，是从顾里开始的。短发、红唇、冷脸，一开口，就像能把整间会议室的温度，降个三度。可是在那之前啊，她其实是华语乐坛里，很有辨识度的一个甜妹。声音清亮、表情灵动，古灵精怪得，像随时会从校园剧里跑出来。",

    "bridge": "今天这一期，就用五首早期的甜歌，带你重新认识她。而其中最贴题、最像一颗小太阳的那一首，我把它放在了第一名。",

    "s1_voice": "如果要用一首歌，证明顾里之前的郭采洁到底有多甜，那一定是这首小太阳。它的甜不腻人，是清爽的甜，像夏天早上一把拉开窗帘，阳光直接扑到你脸上。后来她可以是气场全开的顾里，可在这首歌里，她就是一颗，亮亮的小太阳。",

    "s1_mid": "气场可以后天再长，可这份亮，是她本来就有的。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
Path("sandbox/guocaijie-sweet/audio").mkdir(parents=True, exist_ok=True)
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    out = f"sandbox/guocaijie-sweet/audio/{key}.wav"
    sf.write(out, audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:10s} {meta[key]['dur']:6.2f}s")

Path("sandbox/guocaijie-sweet/audio/sample_narration.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL", round(sum(m["dur"] for m in meta.values()), 2), "s")
