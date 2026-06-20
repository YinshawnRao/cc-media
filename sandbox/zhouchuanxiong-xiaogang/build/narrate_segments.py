#!/usr/bin/env python3
"""周传雄「小刚时期」最5首 — 女声旁白 (zf_xiaoyi)，逐字稿原样。
输出 audio/{hook,s1..s5,outro,cta}_voice.wav（命名对齐 full_build.py）。
最后一段固定为 outro_cta（引流 CTA，硬约束、优先级高于 brief，见 CONVENTIONS「固定结尾配音」）——不删不改、排在 outro 之后。
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outro_cta import FIXED_OUTRO_CTA

ROOT = Path(__file__).resolve().parent.parent
AUD = ROOT / "audio"; AUD.mkdir(exist_ok=True)
VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "hook_voice": "在周传雄唱黄昏、唱尽苦情之前，他还有一个名字，叫小刚。今天我们倒着数，回到那个声音最亮、眼里还有光的少年。",
    # 倒数 5 -> 1
    "s1_voice": "先从第五名说起，舍不得你走。它没有后来那些情歌的撕心裂肺，更像一个年轻人，在刚要失去的时候，那种说不出口、却怎么也放不下的不舍。简单、真挚、不复杂，却特别像我们年轻时，那种不太会表达，但真的舍不得的心情。",
    "s2_voice": "第四名，风干我的悲伤。这是一首越听越懂的小刚遗珠。它的悲伤不浓，反而很清瘦、很干净，不是嚎啕大哭，而是被时间一点一点吹干的失落。那时候的他还没学会把痛唱得很重，只是一个刚刚学会失去的少年，嘴上说得洒脱，声音里却藏不住难过。",
    "s3_voice": "第三名，陪着我一直到世界的尽头。光是这个歌名，就很九十年代的小刚。它不压抑、不心碎，而是带着一股纯情和执拗，把永远这两个字，说得特别认真、特别用力。后来的他更像一个成年人在回望爱情，而这首，是一个少年站在爱情里面，真的相信自己可以陪一个人，走到世界的尽头。",
    "s4_voice": "第二名，吉普赛情人。和哈萨雅琪一样，这是早期小刚最有标签感的作品。旋律、编曲，还有那股气质，都带着九十年代才会有的异域浪漫，不是真的深沉复杂，而是年轻人想象里的自由、热烈和神秘。它不像后来那样把悲伤唱得很重，更像一个男孩，在花花世界里第一次看见爱情，眼睛是亮的，心也是飘的。这，就是很典型的小刚味。",
    "s5_voice": "而第一名，哈萨雅琪。这几乎就是小刚时期的一张声音名片。它最特别的地方，不只是旋律抓耳，而是那种扑面而来的早期偶像感，有异域风，有青春感，还有一点天真又热烈的浪漫。后来的周传雄越来越成熟、越来越苦，但这首歌里的他，还是那个声音明亮、表达直接、带着少年冲劲的小刚。如果要用一首歌，让一个路人明白什么叫小刚时期，这一首，基本绕不开。",
    # 作品 outro：升华，不带投票问句（防双 CTA）
    "outro_voice": "从舍不得你走，到哈萨雅琪，这五首拼出来的，是同一个小刚：声音很亮，眼里有光，把爱情想得简单又用力。后来他写尽了成年人失去的痛，可这些早期的歌留住的，是他还没被岁月磨沉之前，那个最干净、最纯情的少年。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改
    "cta_voice": FIXED_OUTRO_CTA,
}

pipeline = KPipeline(lang_code="z")
total = 0.0
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(AUD / f"{key}.wav", audio, SR)
    dur = round(len(audio) / SR, 3)
    total += dur
    print(f"{key:12s} {dur:6.2f}s")
print(f"TOTAL narration {round(total,2)} s")
