#!/usr/bin/env python3
"""Male narration for 罗志祥最被低估的5首歌.

Ranking is preserved from the brief: #1 幸福不灭, #2 最后的风度,
#3 习惯就好, #4 几分, #5 全城热爱. The video reveals from 05 to 01.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
sys.path.insert(0, str(ROOT.parents[1] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zm_yunxi"
SR = 24000
LEAD_GUARD = "接下来，"
LEAD_GUARD_OVERRIDE = {"intro": "", "outro": "那，"}

BLOCKS = {
    "intro": (
        "提起罗志祥，很多人先想到唱跳、综艺感和舞台爆发。可如果只用这些标签定义他，"
        "就会漏掉一批真正耐听的歌。有些不是最红的主打，有些甚至被同专辑的大歌盖住，"
        "但越听越能看出他的情绪表达。今天这期，从第五名倒数到第一名，盘一盘罗志祥最被低估的五首歌。"
    ),
    "p5_quanchengreai": (
        "第五名，《全城热爱》。它不是绝对冷门，但在罗志祥作品讨论里，经常没有得到足够位置。"
        "比起同阶段更强势的舞曲标签，它更像一首热烈、明亮、适合大合唱的流行歌。"
        "这首歌的好，不只是热闹，而是把他那种偶像型的正能量唱得很自然，放在第五名，刚好补上他作品里被低估的阳光面。"
    ),
    "p4_jifen": (
        "第四名，《几分》。罗志祥的情歌里，有些歌赢在旋律记忆点，有些赢在叙事感，《几分》属于后者。"
        "它写的不是轰轰烈烈，而是关系里那种不确定：还剩几分喜欢，几分遗憾，几分不甘心。"
        "这首歌情绪不爆炸，但很细，罗志祥也没有把每一句都唱成苦情戏，反而更像真实分手后的反复自问。"
    ),
    "p3_xiguanjiuhao": (
        "第三名，《习惯就好》。它不是罗志祥传播最广的苦情歌，但特别适合反复听。"
        "歌名听起来很轻，内容其实很重：不是放下了，而是痛到后来只能假装习惯就好。"
        "这种歌最怕唱得油，或者太用力，可他的版本有一种都市失恋后的疲惫感，像一个人已经不想争辩，只能把难过吞回去。"
    ),
    "p2_zuihoudefengdu": (
        "第二名，《最后的风度》。它收录在《舞所不在》，同一张专辑里有《一支独秀》《我不会唱歌》这种更容易被记住的歌，"
        "所以它很容易被埋掉。它真正准的地方，是分手时那种不体面也要装体面的情绪：明明很痛，还要把最后一点尊严撑住。"
        "罗志祥没有过度卖惨，反而让歌里的失落更真实。"
    ),
    "p1_xingfubumie": (
        "第一名，《幸福不灭》。很多人提到罗志祥，会先想到舞台和综艺，但这首歌很能证明他抒情歌的完成度。"
        "它不是靠高音硬推的情歌，而是有一种很干净、很少年感的真诚。旋律明亮，情绪不苦大仇深，却能唱出我还相信爱的笃定。"
        "它收录在《潮男正传》，也是《篮球火》记忆里很容易被忽略的一首。舞台标签太强，反而挡住了这类真诚的抒情歌。"
    ),
    "outro": (
        "五首歌盘完。第五，全城热爱；第四，几分；第三，习惯就好；第二，最后的风度；第一，幸福不灭。"
        "罗志祥的作品不只有唱跳爆点，也有明亮、克制、疲惫、体面和真诚。"
        "这些被标签盖住的歌，刚好拼出了一个更完整的罗志祥。"
    ),
    "cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        guard = LEAD_GUARD_OVERRIDE.get(key, LEAD_GUARD)
        synth_text = text if key == "cta" else guard + text
        chunks = [audio for _, _, audio in pipeline(synth_text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:22s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
