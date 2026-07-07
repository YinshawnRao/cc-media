#!/usr/bin/env python3
"""Generate narration wavs for 张韶涵最被低估的5首歌（倒数 #5 -> #1）。"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序：05 幻想爱 -> 04 听见月光 -> 03 惊天动地 -> 02 复活节 -> 01 偶尔
# 事实口径：这 5 首都不是张韶涵本人创作，旁白绝不说"她写的"。
BLOCKS = {
    "intro": "提起张韶涵，大家先想到的，多半是隐形的翅膀那种一开口就发光的励志大歌。可她真正动人的，还有藏在专辑深处、被这些大歌盖住的另一面。今天这五首，是张韶涵最被低估的五首歌。",
    "p5_huanxiangai": "第五名，幻想爱。它不写现实里的痛，也不写舞台上的燃，写的是一个女孩，对爱情的幻想和想象。气质轻盈、梦幻，还带着一点小小的任性。它不算厚重，却把少女张韶涵那份天马行空的灵气，完整地留了下来。",
    "p4_tingyueguang": "第四名，听见月光。这是张韶涵很早期的作品，干净得像一阵风。月光不是被看见，而是被听见，光本身好像就有了声音。它不抢、不炸，却特别耐听，把她刚出道时那种清澈、透明、像做梦一样的声音，轻轻保存了下来。",
    "p3_jingtiandongdi": "第三名，惊天动地。它收在潘朵拉那张专辑里，旁边就是隐形的翅膀、香水百合、口袋的天空，实在太容易被盖住。可它其实很有爆发力，带着戏剧感和大场面。副歌一打开，你能听见一种少女英雄式的能量，从她的高音里直接冲出来。",
    "p2_fuhuojie": "第二名，复活节。光是这个歌名，就已经很特别。它唱的不是普通的失恋，而是从枯萎、破碎、失去里，重新站起来。明明已经受了伤，却还想让自己，重新活一次。你能听见她声音里那股又亮又倔的生命力，脆弱，但绝不认输。",
    "p1_ouer": "第一名，偶尔。它必须排第一。这是后期更成熟的张韶涵，唱的不是天天崩溃的痛，而是偶尔想起、偶尔失落，偶尔发现，自己其实还没有真的放下。她明明有最有穿透力的嗓子，这一次却把情绪压得很轻。越轻，后劲越长。",
    "outro": "从幻想爱、听见月光，到惊天动地、复活节，再到偶尔。张韶涵从来不只是那个唱励志大歌的天后，她的专辑深处，还藏着这么多又倔、又透明的遗珠。这五首，刚好补全了被翅膀的光芒盖住的，另一个张韶涵。",
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3), "voice": VOICE}
        print(f"{key:20s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
