#!/usr/bin/env python3
"""女声 zf_xiaoyi。吴青峰为别人写的歌 TOP5（倒数 #5->#1）。
段：intro + 5 首转场旁白(按歌 key) + outro。无中段 VO（展示段纯音乐）。
口播"第N、《歌名》"排名播报 OK；无 meta 倒数旁注；无英文（Kokoro 不擅中英混读）。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"   # 女声（用户指定）
SR = 24000
SPEED = 0.97          # 略稳，保留盘点推进感

BLOCKS = {
    "intro": "他写过太多动人的歌。可你或许不知道，华语乐坛有一整排耳熟能详的金曲，握着笔的那个人，都是吴青峰。他写给别人的歌，常常比写给自己的，更敢，也更狠。今天这五首，全是他为别人量身打造的作品。看他，怎么把一个又一个名字，写成经典。",

    # 倒数第五 怪美的（蔡依林 2018，词吴青峰）
    "guaimei": "第五名，蔡依林的《怪美的》。这是吴青峰写词的另一张面孔。不再是清冷的诗意，而是尖锐、自嘲，带着反击，也带着重建。他把那些被审视、被定义的刺痛，写成了一句句强硬的宣言。放进蔡依林的世界里，刚刚好。",

    # 倒数第四 年轮说（杨丞琳 2015，词吴青峰/曲郑宇界）
    "nianlun": "第四名，杨丞琳的《年轮说》。这一首的厉害，全在词。吴青峰把一段感情，写成了一圈一圈的年轮。剖开来，是成长，也是伤痕。它不靠苦情取胜，而是靠文字，一层一层，慢慢沉进你的心里。",

    # 倒数第三 掉了（张惠妹/阿密特 2009，词曲吴青峰）
    "diaole": "第三名，张惠妹的《掉了》。吴青峰把失去，写得很碎、很轻；而阿妹，把它唱得很重。亲情、遗憾，还有告别，被他压进同一首歌里。情绪浓到，几乎握不住。这也是公认，最见功力的一首。",

    # 倒数第二 带我走（杨丞琳 2008，词曲吴青峰）— 跨时代衔接（footage 用近年 Live）
    "daiwozou": "第二名，杨丞琳的《带我走》。这是吴青峰写给别人、最出圈的情歌之一。旋律一响起，就是一整个青春。它的悲伤不吵不闹，却在很多年以后，依然被她一遍又一遍地唱起。那种被留下的后劲，原来一直都在。",

    # 倒数第一 有形的翅膀（张韶涵 2012，词曲吴青峰）— 压轴；footage 用 张韶涵feat吴青峰同台合唱版
    "youxing": "第一名，张韶涵的《有形的翅膀》。它的传唱度，几乎不需要介绍。它像是《隐形的翅膀》之后，吴青峰写下的一次回应。把励志，从一个人咬牙硬撑，唱成了，有人陪你，一起飞。温暖，坚定，也最张韶涵。而多年以后，当他们俩并肩，再一次唱起这首歌，你就会明白，为什么，是它。",

    "outro": "五首歌，五个名字，背后，是同一支笔。吴青峰把那些最好的句子，慷慨地，写给了别人。如果这里面，也有一首歌，曾经陪过你，记得在评论区告诉我。你心里的第一名，是哪一首？",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:12s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL VO", round(sum(m["dur"] for m in meta.values()), 2), "s")
