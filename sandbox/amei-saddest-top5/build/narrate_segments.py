#!/usr/bin/env python3
"""Generate female narration wavs for 张惠妹最苦的5首歌 (countdown 5->1, zf_xiaoyi).

文案据用户给的歌曲描述打磨成自然口播；开头不公布排名；规避英文（Kokoro 中英混读会断）。
倒数揭晓：连名带姓⑤ → 掉了④ → 剪爱③ → 我恨我爱你② → 人质①。
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "张惠妹的嗓子，是华语乐坛最能扛情绪的那一把。可她最苦的歌，往往不是声嘶力竭，而是把痛唱得特别克制。这五首，我们先不公布排名，从第五名开始，一首一首往回数。",
    "lianmingdaixing": "第五名，《连名带姓》。它苦在一种成年人式的旧伤复发。平时好像已经没事了，可只要那个名字，被完完整整地念出来，过去就又一次被叫醒。这首收在《偷故事的人》里，由周杰伦谱曲、葛大为填词，也是整张专辑里讨论度最高的一首。",
    "diaole": "第四名，《掉了》。它不是传统意义上的苦情歌，而是失去之后，整个人慢慢被掏空的那种感觉。《阿密特》时期的阿妹，更像是在一刀一刀剖开自己，唱法更冷，也更撕裂。它的苦不热闹，像回音消失之后，房间突然安静下来。",
    "jianai": "第三名，《剪爱》。它苦在主动切断。不是不爱了，而是太痛了，痛到只能把这段关系，亲手剪掉。比起还在追问的那些歌，它更狠一点，因为它已经不问了，而是开始自己处理伤口。苦得很直接，却还没到窒息。",
    "wohenwoaini": "第二名，《我恨我爱你》。它比很多苦情歌都更内伤。因为它不是等不到答案，而是答案早就很清楚了，自己却怎么也放不下。恨的真的是对方吗？更像是，恨自己居然还爱着。《真实》这张专辑，本就重新定义了她更内敛的情歌，而这一首，最适合放进苦歌榜。",
    "renzhi": "第一名，《人质》。它的苦，不是失恋，而是被一段关系彻底困住。明明知道，相爱早就变成了互相消耗，却还是舍不得挣扎。《我要快乐？》是阿妹走出低潮、重新回到高峰的一张专辑，而《人质》，正是里面情绪最重、最让人喘不过气的那一首。",
    "outro": "最后，把这份榜单完整地列一次。第五，《连名带姓》。第四，《掉了》。第三，《剪爱》。第二，《我恨我爱你》。第一，《人质》。张惠妹最苦的，从来都不是声嘶力竭的那一种，而是克制底下，那一句始终没说出口的，放不下。",
    # 固定结尾 CTA（全系列统一，逐字照念，全片最后一句；见 CONVENTIONS「固定结尾配音」）
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
