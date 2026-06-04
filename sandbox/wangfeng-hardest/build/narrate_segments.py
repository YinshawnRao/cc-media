#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，汪峰最难的5首歌 / 倒数 5→1。
片头不剧透排名，片尾口播完整难度榜。逐字稿原样。输出 audio/<key>.wav + narration.json。
注意：文本不含英文字母/音名（Kokoro misaki[zh] 念英文会断），音高难度用中文描述，音名只放画面标签。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到汪峰，你可能先想到的是热搜和段子。可只要他一开嗓你就会发现，他是华语摇滚里嗓子最能扛的那一个。他的歌难就难在，副歌一上来就是持续的高音轰炸，还得带着嘶吼的劲往前冲，唱到一半就开始缺氧。今天我们盘点，汪峰最难唱的五首歌。从第五名，开始。",
    "p5_yaobai": "第五名，《一起摇摆》。很多人低估它，以为只是首现场气氛歌。可它是典型的持续轰炸型，一百多个高音密集砸下来，对气息和体能的要求高到离谱。它没有史诗感，但唱到最后你会发现，跟着一起摇摆的不是嗓子，是你的血氧。",
    "p4_yonggan": "第四名，《勇敢的心》。这是著名的高位折磨曲。它最难的不是某一个炸裂的高音，而是高音区一待就是一长段，咬字要硬，情绪还得一路往前顶。越往后越像体能测试，普通人撑到副歌第二遍，那颗勇敢的心，往往先怂了。",
    "p3_cunzai": "第三名，《存在》。这首歌大家都会哼上两句，可真要完整唱下来，没几个人扛得住。副歌那句，我该如何存在，一句比一句高，死死顶在男声的高压区，既要力量，字头还不能糊。多数人唱到这里，想的已经不是如何存在，而是如何换歌。",
    "p2_dengdai": "第二名，《等待》。这首是撕裂唱法的代表作。它的高音不是亮出来的，是吼出来的，可还不能散、不能垮，更不能让人听出来像是真破音。在嘶吼和失控之间走钢丝，这条线，普通人基本没法复刻。",
    "p1_guangming": "第一名，《光明》。汪峰难度的天花板。整段副歌就是一场持续的高压作战，强声咬字，情绪爆发，还得稳稳站住。最怕的就是前面用力过猛，到后面，光明还没寻到，声音先没了。这一首，公认最难。",
    "outro": "所以汪峰，从来不只是热搜上的那个汪峰。这五首歌，他把高音、嘶吼和体能，逼到了普通人够不到的地方。最后再帮你理一遍这份难度榜，第五，一起摇摆，第四，勇敢的心，第三，存在，第二，等待，第一，光明。这里面，你心里真正的天花板，是哪一首？评论区告诉我。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:14s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
