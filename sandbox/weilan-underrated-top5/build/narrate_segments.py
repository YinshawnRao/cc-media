#!/usr/bin/env python3
"""Male narration for 卫兰最被低估的5首歌.

Countdown order is 5 -> 1:
爱深过做人, 他不惯被爱, 爱没有假如, 杂技, 如水.

Long lines use a short spoken guard phrase before synthesis to avoid the Kokoro
long-segment opening drop noted in CONVENTIONS.md. The source text recorded in
narration.json remains the intended script.
"""
from __future__ import annotations

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
GUARD = "接下来，"

BLOCKS = {
    "intro": (
        "很多人想到卫兰，会先想到《大哥》《心乱如麻》这些更出圈的歌。"
        "但她真正厉害的地方，是把很轻的声音，唱出很深的情绪。"
        "今天从第五名倒数，盘一盘卫兰最被低估的五首歌。"
    ),
    "p5_aishenguozuoren": (
        "第五名，《爱深过做人》。这个歌名一听就很港乐，夸张、宿命，也有一点不清醒。"
        "它不如《大哥》《心乱如麻》那么全民熟，"
        "但很能体现卫兰早期情歌里那种，明知道不该沉下去，还是沉下去的声音质感。"
    ),
    "p4_tabuguanbeiai": (
        "第四名，《他不惯被爱》。卫兰最动人的地方，不只是唱被伤害，"
        "而是能唱出那种，我知道对方不够好，但我还是理解他的复杂感。"
        "标题已经很有故事，不是控诉，而是把一个不懂接受爱的人，唱得可怜，也可气。"
    ),
    "p3_aimyoujiashe": (
        "第三名，《爱没有假如》。它不算绝对冷门，"
        "但在卫兰代表作讨论里，经常没有得到应有位置。"
        "旋律很港乐，情绪很直接，可她没有唱成苦情大戏，"
        "而是唱出一种已经知道没得回头，却还是忍不住想的失落。"
    ),
    "p2_zaji": (
        "第二名，《杂技》。很多人说卫兰会唱情歌，"
        "但这首更能听出她处理关系失衡的能力。"
        "爱情像杂技，表面维持平衡，里面全是危险动作。"
        "她唱的不是撕裂，而是明明快撑不住，还要装作稳住。"
    ),
    "p1_rushui": (
        "第一名，《如水》。它不是卫兰最出圈的歌，"
        "却很能代表她最厉害的地方，声音很轻，情绪很深。"
        "它的难点，是不能哭腔太满，也不能唱得太淡，"
        "要让遗憾像慢慢退潮一样留下来。放第一名，我觉得刚刚好。"
    ),
    "outro": (
        "五首歌盘完。第五，爱深过做人；第四，他不惯被爱；第三，爱没有假如；"
        "第二，杂技；第一，如水。"
        "卫兰被低估的，不是音色，而是她总能把遗憾、忍耐和退潮后的空白，唱得特别轻，却特别痛。"
    ),
    "outro_cta": FIXED_OUTRO_CTA,
}


def synth_text(key: str, text: str) -> str:
    if key == "outro_cta" or len(text) < 42:
        return text
    return GUARD + text


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        speak = synth_text(key, text)
        chunks = [audio for _, _, audio in pipeline(speak, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "synth_text": speak, "dur": round(len(audio) / SR, 3)}
        print(f"{key:22s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
