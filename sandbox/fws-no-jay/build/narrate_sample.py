#!/usr/bin/env python3
"""样片旁白 (男声 zm_yunxi)。intro + 第1首《一直很安静》voice + 短评mid。
输出 audio/<key>.wav + narration_sample.json。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000

BLOCKS = {
    # 开场钩子旁白（铺在意象/关键词蒙太奇上，不剧透歌单）
    "intro": "很多人以为，方文山的名字，只会和周杰伦一起出现。"
             "但其实，离开周杰伦的旋律，他也写过很多人的青春、江湖和爱情。"
             "这一期，我们只看一个严格的范围：方文山作词，但周杰伦完全没有参与创作的歌。",
    # 第一首《一直很安静》——副歌前的引入旁白
    "s1_voice": "第一首放它，基本没有争议。"
                "很多人记住它，是因为仙剑奇侠传里的意难平。"
                "但很多人忘了，这种安静到近乎卑微的爱，也是方文山写的。",
    # 第一首 短评（副歌余韵段叠的一句点评）
    "s1_mid": "没有华丽的辞藻，也没有大开大合。"
              "他只是把一个人，站在爱情边缘的沉默，写得很痛。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:10s} {meta[key]['dur']:6.2f}s")

Path("narration_sample.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL", round(sum(m["dur"] for m in meta.values()), 2), "s")
