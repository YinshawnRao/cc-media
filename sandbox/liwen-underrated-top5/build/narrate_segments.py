#!/usr/bin/env python3
"""Male narration for 李玟（CoCo Lee）最被低估的5首歌.

Countdown 5 -> 1 (#1 = 默默爱你, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 《Sunny Day 好心情》= 1998.06（含 默默爱你 / 答案 / 不爱你了）。
- 《Di Da Di 暗示》= 1998.01（含 过完冬季：楼南蔚 词 / 李正帆 曲）。
- 《Promise 承诺》= 2001.10（含 爱你是大麻烦；同碟主打 So Crazy / Baby 对不起）。
- 答案 = 姚谦 词 / 鲍比达 曲，杨凡电影《美少年之恋》主题曲。
- 默默爱你 = 邬裕康 词 / Jim Lee（李伯杰）曲。
- 李玟均为「演唱」，非词曲创作 → 文案不得说"她写的"。
英文专辑名/歌名（Sunny Day / Di Da Di / Promise / So Crazy ...）一律不进配音
（Kokoro 中英混读差），口播一律用中文（好心情 / 暗示 / 承诺 / "更红的主打"），
英文只进屏幕 meta 卡。固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。
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
    "intro": "提到李玟，你会先想到什么？也许是那个站上奥斯卡舞台、把华语流行唱给全世界听的天后，是《暗示》《好心情》那个时期，热辣、自信、永远在发光的她。可在那些国际化的舞曲之外，李玟其实还有另一面，安静、深情，被很多人错过。今天这一期，我们从第五名倒数，盘一盘李玟最被低估的五首歌。",
    "p5_dmf": "第五名，《爱你是大麻烦》。它收在二零零一年的专辑《承诺》里，可大家的注意力，几乎都被专辑里更红的那几首主打带走了，这一首反而像被悄悄藏起来的轻快遗珠。它不是那种大开大合的情歌，而是带点俏皮、带点律动，唱的是恋爱里那种又甜又麻烦的小情绪。李玟的声音在这种歌里特别有弹性，松弛、灵动，会让你一下子想起，她也很会唱这种活泼、可爱的一面。",
    "p4_buai": "第四名，《不爱你了》。它来自一九九八年的《好心情》，歌名看起来很直接，可真正好听的地方，是它没有把不爱了，唱成一句洒脱的口号。她唱的，是一段关系走到尽头之后，那种清醒又疲惫的心情。比起同张专辑里更明亮、更好传播的歌，这首情绪更往里收，也更适合老歌迷，安安静静地慢慢听。原来李玟不是只能唱热情和性感，她唱这种冷下来之后的伤感，一样很有味道。",
    "p3_daan": "第三名，《答案》。它同样收在一九九八年的《好心情》里，由姚谦填词、鲍比达谱曲，还是香港导演杨凡，电影《美少年之恋》的主题曲，所以天生就带着一股电影感。它不是第一耳朵就热闹起来的歌，而是慢慢把问题、等待，和那份说不清的不确定，一点一点推到你面前。李玟唱这种歌很有优势，既有流行女声的明亮，又有节奏蓝调那种细腻的气息和转音，从不把情绪唱得太直白。",
    "p2_guodong": "第二名，《过完冬季》。它来自一九九八年的《暗示》，可同张专辑的同名主打实在太红，大众的记忆几乎都被它带走了。《过完冬季》其实是一首很值得重听的慢歌，旋律拉得很长，情绪压得很沉，唱的是熬过一段冷下来的感情，也熬过一整个冬季。等到冬天真的过完，心里却未必真的放晴。这不是李玟最热辣、最国际化的那一面，而是更安静，也更深的她。",
    "p1_momo": "第一名，《默默爱你》。它同样收在《好心情》里，可同张专辑里那些更好记的歌，把它整个盖了下去。但这一首，最能体现李玟节奏蓝调情歌里最迷人的一面：不是大开大合的苦情，而是温暖、细腻、带着律动，把爱意一点一点，慢慢地唱出来。她的声音在这首里很柔，却一点都不软，越听越能听见那种甜里带深情的质感。这，才是最被低估的李玟。",
    "outro": "五首歌盘完。第五，爱你是大麻烦；第四，不爱你了；第三，答案；第二，过完冬季；第一，默默爱你。李玟从来不只是那个站在国际舞台上、热辣又耀眼的流行天后。在那些大热的舞曲背后，她还有一把温柔、深情、被太多人低估的嗓子。这些被光芒盖住的遗珠，刚好让我们重新听见，一个更安静，也更动人的她。",
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
