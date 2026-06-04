#!/usr/bin/env python3
"""丁世光为别人写的歌 TOP5 — 旁白配音（女声 zf_xiaoyi，倒数盘点）。
按段切：intro + 5 首倒数转场(voice s5->s1) + outro。副歌展示段不放旁白(纯音乐)，收束用屏幕金句字幕。
开头不剧透排名；倒数中口播"第五…第一"是排名播报(允许)；outro 排名靠画面揭晓，旁白只做情感收束。
铁律：无英文/字母混读(Kokoro 不擅长)——Catherine/S.H.E/OST/R&B 一律改写；无 meta 文案。
"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"   # 女声（brief 要求女性配音）
SR = 24000
SPEED = 0.96          # 稍慢，盘点/纪录片感

BLOCKS = {
    # 开场：立题"歌的背面=丁世光"，不剧透排名
    "intro": "有些名字，常年待在歌的背面。丁世光，就是其中很特别的一个。他自己也唱歌，但更多时候，他把写得最好的旋律，留给了别人。今天这五首，都是他写给别人的歌。听完也许你会发现，原来那几首你单曲循环过的，背后都是同一支笔。",

    # 05 讽刺的情书 田馥甄（词曲编曲 丁世光）
    "s5": "第五名，田馥甄的《讽刺的情书》。词、曲、编曲，全部出自丁世光一个人的手，所以它的风格格外完整。它传唱的时间不算最长，可田馥甄的声音，和这段旋律的气质，几乎严丝合缝。越听，越能摸到创作者本人的痕迹。",

    # 04 肋骨 周笔畅（曲 丁世光 / 词 小寒）
    "s4": "第四名，周笔畅的《肋骨》。丁世光作曲，小寒填词。周笔畅的声线，把这首歌唱得很有骨感，克制里又带着力气。那种慵懒、又一点点勾人的旋律味道，正是丁世光的拿手。它算不上最大众的爆款，但在歌迷心里，一直很有分量。",

    # 03 爱来过 S.H.E（曲 丁世光 / 词 施人诚）——避开"S.H.E/OST"字母，用描述
    "s3": "第三名，《爱来过》，丁世光作曲，施人诚填词。原唱，是当年那个红遍两岸的三人女团。这首歌有着一线团体的国民度，又裹着一层偶像剧主题曲的滤镜，路人缘特别稳。它不是她们最炸的那几首，可旋律够抓耳，情绪够青春。",

    # 02 Catherine 陶喆（曲 丁世光）——避开英文歌名，用"写给母亲的歌 / 太平盛世"
    "s2": "第二名，陶喆那首写给母亲的歌，收在专辑《太平盛世》里，由丁世光作曲。它的传唱度，未必是最大众的，但在丁世光的履历里，意义非常重。当年，正是这一首，让很多乐迷第一次，记住了丁世光这个名字。一种幕后的人，终于被听见的故事感。",

    # 01 心酸 林宥嘉（曲/编曲 丁世光）——压轴
    "s1": "第一名，林宥嘉的《心酸》。作曲和编曲，都是丁世光。这几乎是他写给别人的歌里，综合传唱度最高的一首，也是很多人心里，绕不开的那个第一。林宥嘉把它唱成了青春里的遗憾，旋律不靠大开大合，却越听，后劲越上来。那种心酸，是慢慢漫上来的。",

    # 结尾：排名靠画面揭晓，旁白做情感收束（不念英文歌名）
    "outro": "把这五首放在一起你会发现，丁世光写给别人的歌，从来不只是换个人唱那么简单。他把自己的旋律、情绪，还有对每一个歌手的理解，重新长成了另一种样子。也许下一次，当你又单曲循环某一首歌的时候，会忽然想起，它的背面，站着同一个名字。",
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
