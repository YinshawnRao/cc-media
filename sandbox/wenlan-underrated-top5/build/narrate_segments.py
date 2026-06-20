#!/usr/bin/env python3
"""Female narration wavs for 温岚最被低估的5首歌."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": (
        "提到温岚，很多人会先想到《屋顶》《夏天的风》和《祝我生日快乐》。"
        "但她早期声音里最锋利、最有冲劲的那一面，常常藏在没那么路人化的歌里。"
        "这期按排名倒数揭晓，五首温岚最被低估的遗珠，从第五名听到第一名。"
    ),
    "p5_aitaiji": (
        "第五名，《爱太急》。它藏在《有点野》的最后，很容易被前面的《北斗星》"
        "和《动心》盖住。可这首的情绪很完整：爱得太快、太满、太急，最后反而把关系推向失控。"
        "它不是第一耳爆款，却很有温岚早期那种又倔又软的质感。"
    ),
    "p4_buchaobunao": (
        "第四名，《不吵不闹》。它来自《蓝色雨》，没有标题曲那么容易被记住，"
        "也不靠爆点抓人。它好在很克制，唱的是一段关系已经冷下来以后，"
        "连争吵都没有力气的状态。温岚唱这种慢慢收住的 R and B，其实很有味道。"
    ),
    "p3_dongxin": (
        "第三名，《动心》。它有一定知名度，但相比《屋顶》，一直没有被放到应有的位置。"
        "它同样有早期华语 R and B 的质感，动人的地方不是大开大合，"
        "而是两个人慢慢靠近时，那种暧昧、试探和心跳。放到今天听，依然不土。"
    ),
    "p2_lianggewo": (
        "第二名，《爱你的两个我》。它藏在《温式效应》里，常被《祝我生日快乐》"
        "和《夏天的风》盖住。它写的是关系里的分裂感：一个自己还想继续爱，"
        "另一个自己已经快撑不下去。温岚没有把它唱成单纯卖惨，而是把拉扯唱得很真实。"
    ),
    "p1_huangtang": (
        "第一名，《荒唐》。这首不是温岚最路人化的热门歌，但情绪非常狠。"
        "它不是小女生式难过，而是爱到最后才发现一切都很荒唐的清醒和疼。"
        "温岚早期的冲劲，刚好把倔强、挣扎和不甘都唱出来了。"
    ),
    "outro": (
        "最后把排名一起理一遍。第五，《爱太急》；第四，《不吵不闹》；"
        "第三，《动心》；第二，《爱你的两个我》；第一，《荒唐》。"
        "温岚被低估的，从来不是嗓音条件，而是她能把柔软唱出力量，"
        "也能把苦情唱出锋利的那一面。"
    ),
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
        print(f"{key:16s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
