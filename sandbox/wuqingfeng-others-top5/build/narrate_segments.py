#!/usr/bin/env python3
"""吴青峰为别人写的歌 TOP5 — 旁白配音（男声 zm_yunxi，创作者盘点感）。
按段切：intro + 5 首引入(voice) + outro。副歌展示段不放旁白(纯音乐)，收束用屏幕金句字幕。
无英文(Kokoro 不擅中英混读)、无 meta 文案。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
SPEED = 0.95  # 稍慢，盘点/纪录片感

BLOCKS = {
    # 开场：快速立题，引出「这些歌都来自同一支笔」
    "intro": "吴青峰写给自己的歌，常常轻、怪、美，像一个很完整的个人宇宙。但他写给别人的歌，也很有意思。同样是他的旋律和文字，换一个歌手唱出来，就会长成完全不同的样子。这一期，就来听听，他写给别人的，五首歌。",

    # 01 有形的翅膀 张韶涵（词曲 吴青峰）
    "s1": "排在第一的，是张韶涵的《有形的翅膀》。这首主要看大众传唱度，和作品的辨识度。它像是《隐形的翅膀》之后的一次回应，把励志，从一个人咬牙撑住，唱成了，有人陪你一起飞。",

    # 02 带我走 杨丞琳（词曲 吴青峰）
    "s2": "第二名，杨丞琳的《带我走》。这是吴青峰写给别人，最出圈的情歌之一。旋律一出来，几乎就是偶像剧时代的记忆。悲伤，但不狗血，越听，越有一种被留下来的，后劲。",

    # 03 掉了 张惠妹（词曲 吴青峰）
    "s3": "第三名，张惠妹的《掉了》。这首厉害的地方，是青峰把失去，写得很碎，而阿妹，又把它唱得很重。它不只是普通的伤感情歌，更像把亲情、遗憾和告别，一起压进了，声音里。",

    # 04 年轮说 杨丞琳（词 吴青峰 / 曲 郑宇界）
    "s4": "第四名，杨丞琳的《年轮说》。这首歌最强的，是词。吴青峰把爱情，写成了时间的剖面。一圈一圈，切开回忆；也一圈一圈，看见成长，和伤痕。",

    # 05 怪美的 蔡依林（词 吴青峰）
    "s5": "第五名，蔡依林的《怪美的》。这是吴青峰写词能力的，另一种打开方式。它不再只是清冷的诗意，而是尖锐、自嘲、反击，和自我重建。刚好，也非常贴合蔡依林的，表达体系。",

    # 结尾
    "outro": "这五首放在一起，你会发现，吴青峰写给别人的歌，并不是简单换个人唱。而是把他的文字、旋律，和对每一个歌手特质的理解，重新长成了，另一种样子。",
}

pipeline = KPipeline(lang_code="z")
Path("audio").mkdir(exist_ok=True)
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:8s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
