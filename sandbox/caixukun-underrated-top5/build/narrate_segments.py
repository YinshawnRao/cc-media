#!/usr/bin/env python3
"""Male narration for 蔡徐坤最被低估的5首歌.

Countdown 5 -> 1. The fixed CTA is imported from tools/video/outro_cta.py (repo-level
convention). English song titles read awkwardly in Kokoro 中英混读, so RIDE OR DIE /
Hug me are SPOKEN by their Chinese names (至死不渝 / 抱我) — the English titles live
only in the on-screen labels. "Home" has no Chinese name and is kept as the single
English word.
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
    "intro": "提到蔡徐坤，很多人先想到的，是顶流，是话题，是舞台上一个又一个大爆款。可把这些标签放到一边，认真去听他的歌，你会发现，他的作品里，其实藏着不少被严重低估的遗珠。今天我们从第五名倒数，盘一盘蔡徐坤最被低估的五首歌。",
    "p5_meiyouyiwai": "第五名，《没有意外》。比起《情人》那种带着暧昧氛围的出圈作品，这一首更安静，也更细腻。它不靠夸张的编曲，而是把深情和决绝，放在一个很克制的位置。还来不及爱，也来不及怪，他唱失去，不喊不闹，却特别戳人。作为遗珠，它刚好补上了蔡徐坤抒情、收敛的那一面。",
    "p4_rideordie": "第四名，《至死不渝》。这一首，风格上的野心特别明显。战鼓、管风琴，加上嘶吼式的人声，像一部三幕剧，把逆境里死扛的那股劲，做成了一场沉浸式的现场。它不是情歌，也不是单纯的舞曲，而是一首带着舞台剧感的态度作品。路人未必会第一个点开，可放回他的作品脉络里，它真的值得被重新听见。",
    "p3_ganshouta": "第三名，《感受她》。它的优势不是话题，而是音乐性。复古的爵士律动，松弛的咬字，一到现场，即兴感更是直接拉满。这不是一首普通的偶像流行歌，而是更考验氛围和表达的作品。它被低估，只是因为不够热搜，但懂音乐的人，一耳朵就能听出里面的讲究和细节。",
    "p2_hugme": "第二名，《抱我》。它不是最出圈的那一类，却特别耐听。整首歌是慵懒的律动，又带着一点轻快和夏天的味道，不刻意制造爆点，而是松弛地，把亲密和陪伴讲给你听。路人可能记不住，但喜欢的人会觉得，这首歌听起来，真的很舒服，也很有画面。",
    "p1_home": "第一名，《Home》。它不像别的歌，有那么明显的流行爆点，也不是炸场的舞台型作品，而是一首更温暖、更内敛的歌。钢琴、童声，再加上公益的叙事，让它有一种少见的、属于一群人的情绪。不靠暧昧，不靠舞蹈，只是把回家、被接住的那种感觉，唱得特别真。在他的作品里，这一首太容易被更抓耳的单曲盖过，可恰恰是它，让你听见蔡徐坤最柔软、也最真诚的一面。",
    "outro": "五首歌盘完。第五，《没有意外》；第四，《至死不渝》；第三，《感受她》；第二，《抱我》；第一，《Home》。蔡徐坤从来不只是热搜上的那个顶流。把流量和话题放到一边，这些被大热歌盖住的遗珠，藏着他更细腻、更有想法，也更真诚的另一面。",
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
