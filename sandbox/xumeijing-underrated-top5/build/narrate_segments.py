#!/usr/bin/env python3
"""Male narration for 许美静最被低估的5首歌.

Countdown 5 -> 1 (#1 = 迷乱, the climax). 倒数揭晓，按用户给定排名 1~5 反向念出。
事实口径（已核实，见 SOURCES.md，WebSearch 交叉核对 2026-07-02）：
- 迷乱/答案/别走/放你在心里 均收录于《都是夜归人》(1997年1月，上华唱片) 专辑。
- 玫瑰 收录于《蔓延》(1997年12月) 专辑。
- 别走 词曲：陈佳明。其余曲目作词作曲信息未逐一核实，文案不做归属声明。
专辑英文名/外文一律不进配音，只进屏幕字幕。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。
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
    "intro": "提到许美静，很多人先想到的是《城里的月光》《遗憾》这些传唱度极高的歌，那种清醒又带点凉意的都市女声。但在这些大热之外，她还有一批很容易被忽略的好歌，同样冷、同样准，只是没被记住。这一期，我们从第五名倒数，盘一盘许美静最被低估的五首歌。",
    "p5_meigui": "第五名，《玫瑰》，来自一九九七年的专辑《蔓延》。比起《城里的月光》《遗憾》《都是夜归人》这些高辨识度的代表作，《玫瑰》的曝光要小得多，但它的气质很特别：美、带刺，还有一点孤独和危险感。许美静唱这种歌不需要用力渲染，声音一出来，就有一种冷艳又破碎的味道。",
    "p4_fangnixin": "第四名，《放你在心里》，收在一九九七年的《都是夜归人》专辑里。它的情绪很内收：不是把一个人留在身边，而是把这段感情，安静地放进心里。不争、不抢、不吵，这很许美静。它没有特别强的记忆点，却很适合老歌迷重听，因为它唱的，是一种成年人式的放下：不是彻底忘记，而是换一种方式，让这段关系继续存在。",
    "p3_biezou": "第三名，《别走》，同样来自《都是夜归人》，陈佳明作词作曲。歌名很直接，但许美静唱起来，一点也不狗血。她没有声嘶力竭地挽留，而是把别走两个字，压得很低、很冷，也很无力。这更像一段感情快要结束前的最后一句话，没有拉扯，没有控诉，只是安静地承认，自己还舍不得。",
    "p2_daan": "第二名，《答案》，也在《都是夜归人》专辑里。比起标题曲那种直白的孤独感，《答案》更像一首藏在专辑深处的追问：明明很想知道答案，却又害怕答案真的出现。许美静最迷人的地方，就是能把这种矛盾唱得很轻，轻到像没有用力，可后劲却很深。",
    "p1_mailuan": "第一名，《迷乱》，同样收在《都是夜归人》里。这张专辑里，《都是夜归人》《阳光总在风雨后》这些歌记忆点太强，很容易把《迷乱》盖住。但它其实最能代表许美静式的都市冷感：不是嚎啕大哭的伤心，而是一个人在关系里，慢慢迷失方向。她的声音唱这种状态天生有优势，表面很平静，底下却像有暗流在涌动。这，才是最被低估的许美静。",
    "outro": "五首歌盘完。第五，玫瑰；第四，放你在心里；第三，别走；第二，答案；第一，迷乱。许美静从来不只是那个唱《城里的月光》的都市金曲天后，她也很会用最轻、最克制的方式，把心事唱给你听。这些被大热歌盖住的遗珠，刚好补全了她最容易被忽略、也最值得重新听见的另一面。",
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
