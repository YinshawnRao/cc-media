#!/usr/bin/env python3
"""Male narration for 刘若英最被低估的5首歌.

Countdown 5 -> 1 (#1 = 打了一把钥匙给你, the climax). Album/year on screen are
web-verified (brief had several wrong): 我曾爱过一个男孩=我等你2000, 阁楼=到处乱走1996,
透明=很爱很爱你1998, 点亮橘子树=年华2001, 打了一把钥匙给你=雨季1995.
固定 CTA 来自 tools/video/outro_cta.py（仓库级硬约束，永远是最后一句）。
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
    "intro": "说到刘若英，很多人只记得《后来》和《很爱很爱你》。可她最动人的，往往是那些被大热歌盖过的遗珠。今天这一期，盘一盘刘若英最被低估的五首歌，我们从第五名开始。",
    "p5_nanhai": "第五名，《我曾爱过一个男孩》。歌名很直白，故事感却很强。它唱的不是轰轰烈烈的爱情，而是很多年以后回头，才发现那个男孩，一直留在记忆最深的地方。刘若英最难得的，是把怀旧唱得不矫情，只剩下淡淡的、已经过去很久的心动。",
    "p4_gelou": "第四名，《阁楼》。它来自她早期《到处乱走》的年代，气质很文艺，也最像刘若英。阁楼这个意象很妙，像一个放着旧物、心事，还有年轻时没说出口的话的小房间。听这一首，不太像在听流行歌，更像推开一扇很久没进去的门。",
    "p3_touming": "第三名，《透明》。它和那首红遍大街小巷的《很爱很爱你》收在同一张专辑，于是常常被盖了过去。它不抢，像一首安静的小品，把感情里的敏感和无力，唱得很轻。刘若英不靠技巧压人，靠的是那种像真的经历过的语气。",
    "p2_juzishu": "第二名，《点亮橘子树》。它收在《年华》里，同张专辑有《成全》这种太强的大歌，很容易把它盖住。可这一首其实特别有画面感，橘子树、光，还有回忆，像一段很私人的生命片段。它不苦，带着一点童话感，和旧时光的温度。",
    "p1_key": "第一名，《打了一把钥匙给你》。它不是刘若英最路人皆知的情歌，却最能代表她早期那种像在讲故事的质感。钥匙交了出去，关系也像被交付出去一部分。它没有全民级的副歌，可越听，越能听见刘若英最迷人的叙事——不急着哭，也不急着告别，只是把一段感情，慢慢说给你听。",
    "outro": "五首歌听下来你会发现，刘若英最动人的地方，从来不是高音和技巧，而是那种像在跟你讲心事的语气。这些被大热歌盖过的遗珠，刚好补齐了她最被低估的另一面。",
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
