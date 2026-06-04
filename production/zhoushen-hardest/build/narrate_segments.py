#!/usr/bin/env python3
"""男声旁白 (zm_yunxi)，逐字稿原样。输出 audio/<key>.wav + narration.json。
周深最难的5首歌 / 倒数 5→1。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000

BLOCKS = {
    "intro": "提到周深，很多人想到的，是空灵、是天籁，是《大鱼》《光亮》里那种干净到不真实的高音。但你可能没意识到，正是这种听起来很轻松的声音，藏着华语乐坛最难复刻的技术。今天这五首，是公认周深最难唱的歌，普通人连模仿的路径都很难找到。我们从第五名开始。",
    "p5_muyang": "第五，《孤独的牧羊人》。这首更像一场声乐杂技。它用的是约德尔唱法，真假声要在极快的速度里无缝闪切，还有连续的八度大跳。难点不是唱得大声，而是要在飞快的声区跳跃里，保持音准、节奏和那股灵动。唱错一个点，精灵跳舞就会变成嗓子滑倒。",
    "p4_dala": "第四，《达拉崩吧》。它的音高不是最夸张的，但综合难度很离谱。原作者说，这首本来是写给虚拟歌手的，根本没按真人换气来设计。它不只要高音，还要铁肺，结尾那一长串名字，几乎是肺活量的极限挑战。周深还要一个人分饰萝莉、勇者、旁白、巨龙好几个角色，在音色之间反复横跳。",
    "p3_renshi": "第三，《人是_》。这首是听起来就很难，真扒谱更难的类型。E5、F5的高音要连续输出，强混咬字，情绪还要一路往上顶。它不是飘着唱，而是要有电影主题曲那种厚重和压迫感。高音要准，情绪要炸，咬字还不能糊，基本是男声翻唱的大型劝退现场。",
    "p2_guang": "第二，《光亮》。这是周深高音美学的代表作。资料里常提到，这首的头声最高冲到C6，现场那个C6长音被反复讨论。它真正可怕的地方在于，C6不是短促地点一下，而是要在戏腔、古典感和流行表达之间，稳稳地撑住共鸣。唱上去不难，唱得像一道光，才难。",
    "p1_shao": "第一，《少管我》。这首几乎是公认的天花板。民间乐理分析里常说，它的头声最高到D6，比《光亮》的C6还要再往上走一截。但它最恐怖的不只是高，而是这个高音还要唱得又轻、又亮、又稳，不能像是用力冲上去。口哨般的轻盈，配上极限的高位头声，普通人连模仿的路径都找不到。",
    "outro": "所以周深，从来不是只会唱温柔和治愈。在这些歌里，他把高音玩成了一种近乎非人类的技术，轻得像没费力气，难得让人无从模仿。这五首，你心里真正的天花板，是哪一首？评论区告诉我。",
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
