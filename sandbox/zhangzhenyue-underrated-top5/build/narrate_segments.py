#!/usr/bin/env python3
"""Male narration for 张震岳最被低估的5首歌.

Countdown 5 -> 1 (#1 = 破吉他, the climax). 倒数揭晓。
事实口径（已 web 核实，避免文案出错）：
- 张震岳是创作型歌手，这五首词曲都出自他本人 → 可以、也应该说"他写的"（是卖点）。
- 梅雨季 =《跟着感觉走》2025（滚石），张震岳词曲，爵士。
- 两手空空 =《我想要的感觉》2011（滚石），张震岳包办词曲编曲。
- 很难 / 路口 =《OK》2007（陆版改名《思念是一种病》），张震岳词曲。
  ⚠️ 专辑英文名「OK」不进配音（Kokoro 中英混读差）→ 用"和《思念是一种病》《再见》同一张专辑"指代；屏幕卡可写 OK·2007。
- 破吉他 =《我是海雅谷慕》2013（滚石，阿美族名 Ayal Komod 回归专辑），张震岳词曲。
固定结尾 CTA 由 tools/video/outro_cta 提供，永远是最后一句。
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

BLOCKS = {
    "intro": "提到张震岳，很多人先想到的，是《爱我别走》《自由》，是那个唱情歌、也唱青春的阿岳。但他最打动人的状态，常常不在那些大热歌里，而藏在一些被忽略的、不修边幅的作品里。今天这期，我们从第五名倒数，盘一盘张震岳最被低估的五首歌。",
    "p5_meiyu": "第五名，《梅雨季》。它来自二零二五年的《跟着感觉走》，是张震岳近几年特别值得被重新听见的一首。它不像他早期那样直接、粗粝，而是更成熟，也更湿润。梅雨季这个意象选得很准：不是暴雨，也不是晴天，而是情绪一直潮着、闷着，散不开。编曲里带着一点爵士的松弛，像一个人过了很久以后，终于能用比较轻的方式，回头看那一点遗憾。",
    "p4_liangshou": "第四名，《两手空空》。它收在二零一一年的《我想要的感觉》里，词曲都是张震岳自己写的。那张专辑没有他巅峰期的大众热度，里面却有不少更成熟、更松弛的表达。《两手空空》唱的是一种走过以后，才发现自己其实没剩下什么的状态。不是大哭大闹的失败，而是很平静地承认：到最后，好像还是两手空空。它的情绪很淡，后劲却很长。",
    "p3_hennan": "第三名，《很难》。它和《思念是一种病》《再见》收在同一张专辑里，可那几首太强，《很难》就特别容易被路人忽略。但它其实特别阿岳：话说得很直，情绪也不复杂，就是生活真的很难，关系很难，人要继续往前，也很难。他没有刻意煽情，却有一种很实在的疲惫感。张震岳唱这种歌不需要什么华丽技巧，越白话，反而越像生活本身。",
    "p2_lukou": "第二名，《路口》。这首歌有一定的知名度，却长期被《爱我别走》《思念是一种病》这些更强势的作品压住。它最好的地方，是特别有画面感：人生走到一个路口，想往前，又舍不得过去；想转身，又不知道该去哪里。它不是张震岳最热烈的摇滚，也不是最出圈的情歌，却特别能唱出成年人卡在选择里的那种状态。越听，越像一段没有答案的停顿。",
    "p1_pojita": "第一名，《破吉他》。它收在二零一三年那张《我是海雅谷慕》里，词曲也都出自张震岳自己。这首歌不是他最路人化的大热歌，却最能代表他骨子里那种不修边幅、真诚、又有点狼狈的气质。一把破吉他，听起来是个很小的东西，里面却装着很多青春、理想，和生活里的不甘。它不靠精致的编曲取胜，全靠那股粗糙的真实感留下来。张震岳最迷人的地方，常常就是这样：他没把自己包装得多漂亮，可你会愿意相信他唱的每一句。这，就是最被低估的张震岳。",
    "outro": "五首歌盘完。第五，梅雨季；第四，两手空空；第三，很难；第二，路口；第一，破吉他。张震岳从来不只是那个唱大热情歌的阿岳，他更会用最白话、最不修饰的方式，把生活和遗憾，轻轻唱给你听。这些被大热歌盖住的遗珠，刚好补全了他最真实、也最被低估的另一面。",
    "outro_cta": FIXED_OUTRO_CTA,
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
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
