#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)。输出 audio/<key>.wav + narration.json。
谭咏麟最被低估的5首歌 / 倒数 5→1（#1《还是你懂得爱我》压轴）。
用户指定：开头/转场/结尾女性配音 → 全程女声；片头不暴露排名(留悬念)，片尾再列榜单。
TTS 安全：不含英文字母（Kokoro misaki 中英混读差）；怪标点(如 !? )只放屏幕，不进口播。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提起谭咏麟，你会先想起哪一首？是《爱情陷阱》，是《爱在深秋》，还是那首《朋友》。校长的金曲，多到能撑起一整晚的演唱会。可也正因为太多经典压在最前面，有那么几首歌，明明很动人，却始终被挡在聚光灯外，安静地躺在专辑最深的地方。今天这五首，不是他最红的，却可能是最值得你单曲循环的。我们从第五首开始。",
    "p5_hhdsy": "第五，《黄昏的声音》。它当年被收在一张并不算冷门的专辑里，可同碟那几首拿过奖的作品太醒目，把它衬得像被忽略了一样。但这首歌的旋律和氛围，其实特别耐听，像黄昏时分一个人的自言自语，不喧哗，却留着一股老港乐才有的余味。",
    "p4_cknzhc": "第四，《此刻你在何处》。它出自那张太强的《爱情陷阱》。同名主打让谭咏麟站上事业的最高峰，同一张专辑里，还有《幸运星》《情是永远着迷》，每一首都太容易被记住。于是这首完整的电影情歌，就被大热的光芒，悄悄盖了过去。可如今再听，它反而像专辑里被人遗忘的一颗遗珠。",
    "p3_ybxn": "第三，《永不想你》，来自《第一滴泪》。那张专辑有《无言感激》这样的大热压阵，让它没能留下太多存在感。可这首由林敏骢一手包办词曲的作品，最能体现谭咏麟中后期情歌的成熟。它唱的不是少年人的失恋，而是成年人那种，明明已经懂了，却还是放不下。",
    "p2_qsdxx": "第二，《墙上的肖像》。这首歌，很有老歌迷私藏的气质。它不属于谭咏麟最大众的那条旋律线，而是带着一点阴郁，一点艺术感和都市感。在同名专辑里，《痴心的废墟》《曾经》更容易被记住，反倒让这首点题之作，像一幅藏在专辑深处的暗色画。而这张专辑，正是不少乐迷心里最爱的一张。",
    "p1_hsndd": "第一，《还是你懂得爱我》。它不是那种靠副歌瞬间爆开的金曲，而是越听越能品出厚度的成熟情歌。在《笑看人生》里，大家更容易记住前半段明快的作品，可乐评早就点明，整张唱片里最感人的慢歌，正是这一首，甚至称它，是全碟的首选佳作。把它放在第一，是因为最深的那份情，从来都不是喊出来的。",
    "outro": "这就是今天的五首遗珠。第五，《黄昏的声音》；第四，《此刻你在何处》；第三，《永不想你》；第二，《墙上的肖像》；第一，《还是你懂得爱我》。它们都不是谭咏麟最红的歌，却都值得被重新听见一次。这五首里，哪一首，是你也舍不得被埋没的那一首？评论区，告诉我。",
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
