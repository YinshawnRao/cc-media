#!/usr/bin/env python3
"""样片旁白 TTS：封面+开头+第10首《人间》。男声 zm_yunxi（规范默认）。
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
    # 开头（王菲精神地图 + 引入）
    "op1": "王菲，当然有很多好歌。",
    "op2": "但有一种王菲，是林夕写出来的。",
    "op3": "他写给她的，不只是爱情；",
    "op4": "还有孤独，还有放下，还有无常。",
    "op5": "还有，一个人走到世界尽头以后，仍然不解释自己的样子。",
    "op6": "今天这十首，我们不只听旋律，更听林夕，怎么把王菲，一步一步，写成传奇。",
    # 第10首《人间》
    "rj1": "林夕写给王菲的第一层，是人间。",
    "rj2": "这首歌没有太多锋利的隐喻，反而像一句很轻的祝福。",
    "rj3": "王菲一开口，那种疏离感，忽然就落地了。",
    "rj4": "她不是不食人间烟火，她只是，把人间唱得很远，也很温柔。",
    # 转场（进入第9首《红豆》）
    "tr1": "但林夕真正厉害的地方是，他写爱，从来不只写甜。",
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
