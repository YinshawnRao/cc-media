#!/usr/bin/env python3
"""样片旁白 TTS：封面+开头+第8首《没有人》。男声 zm_yunxi（规范默认）。
TTS 文本避免英文(Elva/R&B)——Kokoro misaki[zh] 中英混读会断；屏幕字幕另保留英文。
模型只加载一次，批量生成 audio/<key>.wav。从项目根运行：
  tools/tts/venv/bin/python build/narrate.py
"""
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000

LINES = {
    # ---- 开头（钩子：把 Elva 重新定义成"陈伟做出来的都市女声"）----
    "op1": "很多人记得萧亚轩，是因为她会跳，会唱，会时髦。",
    "op2": "但如果只用，唱跳女歌手，来概括她，其实太浅了。",
    "op3": "真正把这个声音做出来的人之一，是陈伟。",
    "op4": "他写旋律，做节奏，抓声线，也抓住了那个年代，最摩登的都市感。",
    "op5": "所以这一期，我们不聊普通的热门歌单。",
    "op6": "我们聊八首歌，看陈伟怎么一步一步，把萧亚轩，做成千禧年华语乐坛，最特别的都市女声。",
    # ---- 第8首《没有人》：出道冷感、中低音、R&B 底色 ----
    "rj1": "第八首，没有人。",
    "rj2": "它不是那种，一上来就讨好市场的甜歌；而是很直接地，把萧亚轩的中低音，和节奏布鲁斯的底色，推了出来。",
    "rj3": "陈伟在这里做的，不只是写一首歌，而是帮她确认了一个方向。",
    "rj4": "她不是邻家女孩，她是带着距离感，走进华语乐坛的，都市女声。",
    # ---- 转场（引向第7首《突然想起你》）----
    "tr1": "有了这个冷感的底色；到了下一首，想念，也不再是哭哭啼啼，而是城市夜里，突然的一次失神。",
}

out = Path("audio")
out.mkdir(exist_ok=True)
pipe = KPipeline(lang_code="z")
durs = {}
for k, t in LINES.items():
    chunks = [a for _, _, a in pipe(t, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(out / f"{k}.wav", audio, SR)
    durs[k] = round(len(audio) / SR, 3)
    print(f"{k}: {durs[k]}s  {t}")
print("TOTAL voice:", round(sum(durs.values()), 2), "s")
