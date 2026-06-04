#!/usr/bin/env python3
"""女声 zf_xiaoyi。吴青峰冷门遗珠 TOP5（倒数 #5->#1）。
段：intro + 5 首转场旁白（按歌 key）+ outro。无中段 VO（展示段纯音乐）。
无 meta 倒数旁注；逐首"第N，《歌名》"排名播报 OK。无英文（Kokoro 不擅中英混读）。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"   # 女声（用户指定）
SR = 24000
SPEED = 0.96          # 略measured，文学/沙龙气质，但保留盘点的推进感

BLOCKS = {
    "intro": "提到吴青峰，你大概会先想到那些传唱度很高的名字。但真正让人着迷的，往往是另外一些。它们没排在热门歌单的最前面，却被懂他的人，私心珍藏。它们冷门，却很高级；初听不抓耳，越听，却越深。今天这五首，是只属于吴青峰的，遗珠。",

    # 第五 ……睡美人（马拉美的星期二·沙龙·梦境闭幕曲·审美遗珠）
    "shuimeiren": "第五，是收在《马拉美的星期二》里的，睡美人。这张专辑的灵感，来自一场艺文沙龙，每一首歌，都邀来不同领域的音乐人一起完成。睡美人，不是那种一听就懂的入口，它更像整场梦的谢幕曲，文学、沙龙、又梦境化。冷门，却高级得发亮。",

    # 第四 等（册叶一·轻轻唱后劲深·被大概念遮住）
    "deng": "第四，《等》。它来自吴青峰的个人专辑《册叶一》。那是他把过去写给别人的歌，重新收回到自己身上的一次梳理。整张十六首，很多都被更大的概念盖住了光，而《等》，就是其中最该被重新捡起来的一首。它没有锋利的概念，却特别耐听。是青峰最擅长的那一种，轻轻地唱，后劲，却很深。",

    # 第三 译梦机（太空人·七分钟·梦境短片·奇幻想像二部曲·野心大）
    "yimengji": "第三，《译梦机》。它的遗珠感，在于野心太大。七分多钟的长度，早就不是一首流行歌的结构，而更像一部梦境短片。在《太空人》的影像企划里，它和《回音收集员》，被称作奇幻想象二部曲。梦境、动画、现实，来回交错。它不容易被单曲循环，可它的完成度，高得惊人。",

    # 第二 伤风（黑色寓言·尖锐阴暗·当伤害成为一种风气）
    "shangfeng": "第二，《伤风》。这是这份榜单里，最有黑色寓言感的一首。它不是青峰最甜、最仙的那一面，而是更尖锐，也更阴暗的一面。官方曾经解释，这首写的是，当伤害，成为一种风气。这个立意，非常吴青峰。他把整个时代的病，写成了一场，会传染的，伤风。",

    # 第一 线的记忆（压轴·最该被重新听见·没有大副歌但完整·像很细的线·多变镜头）
    "xian": "第一，《线的记忆》。在我心里，这是吴青峰个人作品里，最该被重新听见的一首。它没有用大副歌强行抓你，可旋律、歌词，还有那支影像的气质，完整得像一件艺术品。它像一根很细的线，把孤独、牵连和失去，全都缝在了一起。就连画面，都用不断变化的比例和镜头，去讲，每一根，孤独的线。放在第一，最稳。",

    "outro": "所以你看，吴青峰真正动人的地方，从来都不只在那些传唱度最高的歌里。这五首遗珠，冷门，却各自高级。如果你也听过其中一首，欢迎在评论区告诉我，哪一首，是你心里那颗，最舍不得的遗珠。",
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
