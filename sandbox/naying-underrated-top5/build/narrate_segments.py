#!/usr/bin/env python3
"""Generate female narration wavs for 那英最被低估的5首歌."""
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
    "intro": "提到那英，很多人第一反应会是《征服》《梦一场》，或者那些被反复翻唱的大歌。但她有一些歌，明明很能代表她，却长期被压在热门作品旁边。这一期，我们只聊五首最被低估的那英，从第五名开始，往第一名走。",
    "p5_chuan": "第五名，《船》。它在《我不是天使》时期很容易被《一笑而过》和同名主打盖住。可这首的好，在于不抢。它像一段关系终于离岸，情绪没有特别激烈，却有漂远之后的空。",
    "p4_nideshiwoderen": "第四名，《你是我的人》。它来自《征服》，但那张专辑太强了，同名主打、《梦醒了》、《不管有多苦》，都更容易被记住。相比那些大开大合的歌，这首更和缓，也更安宁，能听见那英声音里很少被路人注意到的柔软。",
    "p3_wanqianli": "第三名，《一万一千公里》。这首冷门感够，也很有千禧年前后华语情歌的文艺气质。林夕的词，李偲菘的曲，加上一点拨弦的点睛，让它不像普通流行歌那么直给。它更像一段很远、很长、到不了的关系。",
    "p2_baisixian": "第二名，《白丝线》。这也是《干脆》里特别值得捡回来的遗珠。它没有《梦一场》那么大众，也没有《愿赌服输》那么有句子记忆点，但唱法和气质很特别。它不是靠热度赢，而是靠质感慢慢留下来。",
    "p1_yuandu": "第一名，《愿赌服输》。这首我会放第一，因为它特别能代表那英那种硬气里的脆弱。歌名就很那英：输也输得明白，不撒娇，不求饶。它在《干脆》里被《梦一场》和《干脆》压住，可真正懂她的人，很难不记得这首歌的劲。",
    "outro": "所以那英被低估的歌，不只是冷门歌单补遗。它们把她声音里的几种侧面摊开：硬气、柔软、距离感、质感，还有那种输也不低头的清醒。热门作品证明她能赢，而这些遗珠，反而更能说明她为什么经得起反复听。",
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
        print(f"{key:20s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
