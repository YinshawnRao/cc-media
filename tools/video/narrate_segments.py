#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "很多人记住张韶涵，是因为《隐形的翅膀》。她好像一直是那个唱希望、唱光、唱梦想的天使嗓音。但如果你只记得这一面，可能真的低估了她。因为张韶涵的歌里，也藏着一个更暗、更燃、更有攻击性的世界。",
    "p1_pandora": "第一首《潘朵拉》。这首歌很适合打开张韶涵的另一面。它不是《隐形的翅膀》那种明亮的希望，而像一个被打开的魔盒，电子摇滚、童话感、神秘感混在一起，清亮声线突然变得很有戏剧张力。",
    "p2_nahan": "第二首《呐喊》。张韶涵最特别的地方，是她的声音明明很亮，却可以唱出一种尖锐的冲击力。这首不是治愈你，而是把压住的情绪直接撕开。",
    "p3_pojian": "第三首《破茧》。这首是张韶涵战斗系的一面。它不是简单励志，而是从噩梦、深渊、撕裂感里往外冲。她的高音在这里不是漂亮，而是像一道直接破开的光。",
    "p4_quanmian": "第四首《全面沦陷》。这首歌的气质很不一样，它不是张韶涵常见的清澈明亮，而是更暗、更沉、更有失控感。她把‘沦陷’唱得不是软弱，而像明知道危险，还是要往里走。",
    "p5_adiao": "第五首《阿刁》。这首不是她自己的原唱作品，但它几乎把张韶涵的生存感唱出来了。她不是在扮演坚强，而是真的把瘦小身体里的倔强、孤独和反击，全部推到了舞台最前面。",
    "outro": "所以张韶涵不是只有《隐形的翅膀》。她当然会唱希望，但她更厉害的地方，是能把黑暗、挣扎、破碎和反击，都唱成一种往上飞的力量。你心里还有哪首张韶涵被低估的暗黑系作品？",
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
