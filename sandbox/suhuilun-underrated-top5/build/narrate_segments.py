#!/usr/bin/env python3
"""Male narration for 苏慧伦最被低估的5首歌.

Countdown 5 -> 1 (#1 = 你来, the climax). 倒数揭晓。
事实口径（已 web 核实，避免文案出错）：
- 你来 = 《鸭子》(1996·滚石)。伍佰 & China Blue 注入另类摇滚气息（编曲/制作），不强说"伍佰作词曲"。
- 叶子落下的世界 = 《鸭子》(1996)。许常德 词 / 陈进兴 曲（非本人创作，文案不说"她写的"）。
- 酿爱 = 《Lemon Tree / 柠檬树》(1996)。小虫 注入抒情节奏蓝调；同碟主打《柠檬树》《被动》更强。
- 哭过的天空 = 原收于《Lemon Tree》(1996)，后被选进《失恋万岁》精选辑(1998) CD2 第一首 → 文案称"精选辑第二张碟"。
- 你有离开的自由 = 《懒人日记》(1999)。张震岳 词曲，专辑第四波主打。
英文专辑/团名（China Blue / R&B / OK!OK!）一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
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
    "intro": "提到苏慧伦，很多人脑子里先冒出来的，是《柠檬树》《鸭子》那个甜甜的、有点古灵精怪的玉女形象。可在那些大热单曲背后，她其实藏了不少更安静、也更成熟的好歌，有一点冷，有一点疏离，越听越有味道。今天这期，我们就从第五名倒数，盘一盘苏慧伦最被低估的五首歌。",
    "p5_ziyou": "第五名，《你有离开的自由》。它来自一九九九年的《懒人日记》，由张震岳一手包办词曲，也是这张专辑的第四波主打。光看歌名就很清醒，不是挽留，也不是纠缠，而是大大方方承认，对方有离开的自由。它没有那种一秒就记住的流行标签，却有一种更成熟、更松弛的关系感，刚好补上苏慧伦不只是甜美百变，也有清醒、独立、轻轻放手的一面。",
    "p4_kuguo": "第四名，《哭过的天空》。这首歌被收在一九九八年那张《失恋万岁》精选辑的第二张碟里，比起精选里那些更出名的歌，它更像一封被悄悄藏起来的失恋后记。它最难得的地方，是情绪一点都不夸张，像雨已经下过，眼泪也已经停了，可天空，还没有真正放晴。苏慧伦唱这种哭过以后的状态，比直接哭出来，反而更有余味。",
    "p3_niangai": "第三名，《酿爱》。它来自一九九六年那张《柠檬树》专辑，可同张专辑里，主打的《柠檬树》和《被动》实在太强，《酿爱》就很容易被排到后面。但它其实很值得单独拎出来重听，小虫在这首歌里，注入了他最拿手的抒情节奏蓝调，让整张以抒情为主的专辑，多了一点西洋的味道。它不是第一耳朵就抓人的那种，却特别能听出，转型期里那个更柔、更细、也更成熟的苏慧伦。",
    "p2_yezi": "第二名，《叶子落下的世界》。它同样收在《鸭子》这张专辑里，没有标题曲那种一下子抓住你的记忆点，可它的画面感特别强，叶子一片片落下，季节悄悄换了，一段关系，也跟着慢慢冷掉。苏慧伦唱这种歌，从来不用力煽情，而是用很轻很轻的声音，把那种失落一点一点唱出来。它不像《鸭子》那么热闹，却更适合真爱粉，在夜里安安静静地，单独重听。",
    "p1_nilai": "第一名，《你来》。它同样来自《鸭子》，可这张专辑里有《鸭子》《爱了就算》这些更好记的歌，《你来》就特别容易被盖过去。但它其实特别有后劲，不是古灵精怪的那种甜，也不是大热主打的那种热闹，而是带着一点冷意和另类摇滚的质感。伍佰和他那支乐团的创作气息特别明显，让这首歌在整张《鸭子》里，越听越有味道。这，就是我心里，最被低估的那个苏慧伦。",
    "outro": "五首歌盘完。第五，你有离开的自由；第四，哭过的天空；第三，酿爱；第二，叶子落下的世界；第一，你来。苏慧伦从来都不只是那个唱《柠檬树》《鸭子》的甜美玉女，她也很懂得，用最轻、最克制的方式，把成长、疏离和轻轻的放手，慢慢讲给你听。这些被大热歌盖住的遗珠，刚好补全了她最安静、也最被低估的另一面。",
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
