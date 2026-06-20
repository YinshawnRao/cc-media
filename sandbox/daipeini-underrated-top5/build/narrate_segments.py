#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 戴佩妮最被低估的5首歌 (countdown 5->1).

Hard rules (see CONVENTIONS):
- Female voice zf_xiaoyi (brief explicitly asks for 女性配音: 开头/转场/结尾).
- Intro must NOT reveal the ranking (cover = title + 作品描述 only). Outro reveals it.
- TTS-safe text: avoid English ("Penny"/"Sony"/"No Penn, No Gain") — Kokoro misaki[zh]
  stutters on inline English. Reference albums descriptively; the exact stylized album
  titles (《No Penn, No Gain》 etc.) live on the on-screen cards, not the spoken line.
- Last spoken line is the FIXED 引流 CTA, verbatim (CONVENTIONS「固定结尾配音」硬约束).
- 作品 outro 不得再自带投票问句（防双 CTA），互动一律交给固定句。
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

# 固定结尾引流 CTA —— 逐字照念，全片最后一句（优先级高于 brief）
FIXED_OUTRO_CTA = "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。"

BLOCKS = {
    "intro": "提到戴佩妮，你可能先想到《你要的爱》和《街角的祝福》。但她最迷人的，往往是那些没做成主打、却越听越上头的歌。这一期，戴佩妮最被低估的五首，我们从第五名开始。",
    # 5 《非诚勿扰》(贼, 2016)
    "p5_feicheng": "第五名，《非诚勿扰》。它来自专辑《贼》，被《钢琴键》《未完不待续》这些更醒目的歌盖了过去，像藏在专辑后段的私藏曲。它不苦情，带着一点疏离，也带着一点清醒，是戴佩妮那种好听、却不讨好市场的写法。",
    # 4 《转眼》(No Penn, No Gain, 2003)
    "p4_zhuanyan": "第四名，《转眼》。它藏在那张入围金曲奖的早期专辑里，没有剧歌的传播，也没有强烈的风格标签，胜在足够真诚。这是一首写给久未联络的老朋友的歌——她能把很轻的生活情绪，唱得一点都不轻浮。多年以后再听到，会有点鼻酸。",
    # 3 《你怎么可以安心的睡着》(纯属意外, 2013)
    "p3_anxin": "第三名，《你怎么可以安心的睡着》。它收在《纯属意外》——就是帮戴佩妮拿下金曲奖最佳国语女歌手的那张专辑。比起同名的主打歌，这一首更锋利，走的是英式摇滚的路子。不是温柔的她，而是带着质问、带着不甘、有点咬牙切齿的她。",
    # 2 《钢琴键》(贼, 2016)
    "p2_gangqinjian": "第二名，《钢琴键》。同样来自《贼》——那张她带着整支乐队，跑到南法、住进一座老庄园里录下来的专辑。大家更容易记得《贼》和《未完不待续》，可《钢琴键》其实最有电影感。情绪不是一下子砸下来，而是像手指慢慢按下去，一颗，一颗，把旧伤弹出来。",
    # 1 《水中央》(No Penn, No Gain, 2003)
    "p1_shuizhongyang": "第一名，《水中央》。这是戴佩妮很早期的歌，却已经听得出，她不想只写安全牌情歌的那点野心。编曲里有一点异域感，有一点水波荡漾，旋律不是第一耳就抓人的那种，可它越听越有画面。它所在的专辑入围过金曲奖，也被选进年度十大，只是大众的记忆，被更好传播的歌带走了。这一首，值得你重新听一次。",
    "outro": "这就是这一期，戴佩妮最被低估的五首歌。从第五到第一：《非诚勿扰》《转眼》《你怎么可以安心的睡着》《钢琴键》，和第一名《水中央》。她最珍贵的地方，从来不是讨好市场的旋律，而是那份诚实——把心里最真的情绪，安安静静地，写进歌里。",
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
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
