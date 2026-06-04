#!/usr/bin/env python3
"""女声 zf_xiaoyi。周王陶林男女合唱神曲PK（倒数 #4->#1）。
段：intro(钩子,不泄漏歌单) + rules(评分维度) + 4首揭晓(heaven/dimples/coral/today) + outro。
口播"第N名/歌名/评分"在对应章节揭晓 OK；intro/rules 不出现任何歌名(悬念硬约束)。
无 meta 倒数旁注；无英文/字母(KTV/Lara/PK 已改写)；评分用中文数字。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
SPEED = 0.97

BLOCKS = {
    # 开场钩子：只点四位男歌手 + PK 问题，绝不出现歌名/合唱对象/排名
    "intro": "周杰伦、王力宏、陶喆、林俊杰。四位华语创作天王，如果每个人，只能派出一首男女合唱代表作。谁，才是男女对唱，最强王者？",

    # 评分规则：维度（权重在画面用评分条呈现），仍不出现歌名
    "rules": "有的歌赢在全民传唱，有的赢在作品质感，有的赢在合唱张力，有的赢在时代记忆。今天先不公布歌单，我们用十分制，从五个维度综合打分：传唱度、时代影响力、获奖榜单、网络口碑，还有男女合唱的适配度。话不多说，一首一首，揭晓。",

    # 第4名 王力宏/张靓颖《另一个天堂》9->8.7
    "heaven": "第四名，王力宏和张靓颖，《另一个天堂》，综合八点七分。这首歌赢的，不是全民场景，而是双强配置。王力宏的旋律线，加上张靓颖的高音辨识度，让它更像一场，真正的男女声对撞。它的传唱度，也许没有前面几首那么夸张，但论完成度和现场质感，它，绝对不虚。",

    # 第3名 林俊杰/蔡卓妍《小酒窝》8.8
    "dimples": "第三名，林俊杰和蔡卓妍，《小酒窝》，综合八点八分。这首歌，几乎就是华语甜歌对唱的标准答案。它不靠复杂的概念，也不靠大开大合的炫技，但副歌一出来，记忆点立刻拉满。论路人传唱度、点唱率，还有那股甜甜的氛围，它，甚至能跟第一名掰手腕。",

    # 第2名 周杰伦/梁心颐《珊瑚海》9.2
    "coral": "第二名，周杰伦和梁心颐，《珊瑚海》，综合九点二分。这首歌不是最热闹的合唱，但可能，是质感最稳的一首。男女声不是单纯撒糖，而是在同一片海里，各自遗憾。旋律、歌词、画面感全部在线，属于越听，越能留下来的经典。",

    # 第1名 陶喆/蔡依林《今天你要嫁给我》9.6
    "today": "第一名，陶喆和蔡依林，《今天你要嫁给我》，综合九点六分。这首歌排第一，基本没什么悬念。它不只是好听，而是直接占住了婚礼、晚会、聚会，这些全民合唱的高传播场景。更关键的是，它还拿过金曲奖，最佳年度歌曲。传唱度、场景力、奖项硬度，全部拉满，放在这一组里，就是王炸。",

    # 结尾：全部揭晓后回顾 + CTA（此处出现歌名 OK）
    "outro": "如果只看甜歌传播，《小酒窝》和《今天你要嫁给我》非常强；如果看作品质感，《珊瑚海》很难被忽视；如果看双强唱功，《另一个天堂》也绝对有排面。这个排名，你认吗？评论区，说出你心里的第一名。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:10s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL VO", round(sum(m["dur"] for m in meta.values()), 2), "s")
