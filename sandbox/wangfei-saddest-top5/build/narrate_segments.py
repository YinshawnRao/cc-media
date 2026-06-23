#!/usr/bin/env python3
"""Generate narration wavs for 王菲最苦的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "王菲最苦的歌，不是把难过唱成眼泪。她越冷，越像已经把情绪压到水面以下。今天这五首，不先摊开答案，我们从第五名往第一名数。",
    "aimei": "第五名，《暧昧》。它苦在没有身份：说不清，等不到，退不掉，连难过都没有一个正式名分。王菲没有把它唱成委屈，而是唱成一种悬浮感。关系不上不下，人也不上不下。",
    "youchai": "第四名，《邮差》。它不是青春遗憾，而是成年人的迟到告别。等过，盼过，也替对方找过理由，最后才承认那封信大概不会来了。最苦的是，我已经知道答案，却还想再等一等。",
    "qizi": "第三名，《棋子》。这首的苦，是关系里的失控感。你以为自己在爱，后来才发现自己只是对方棋盘里被移动的那一颗。它不是哭诉，而是清醒地发现，自己没有主动权。",
    "xiaowangshu": "第二名，《笑忘书》。它不是普通失恋歌，而是一个人试图说服自己，算了吧。她不是不知道要往前走，也不是不懂体面，只是时间爬过身体以后，留下的痕迹只有自己最清楚。",
    "anyong": "第一名，《暗涌》。王菲最苦的歌，我会把它排第一。它不是分手现场，而是关系还没结束，你已经提前听见它坍塌的声音。还没失去，却已经预感到要失去，这种苦，才最王菲。",
    "outro": "最后完整揭晓这份榜单。第五，《暧昧》。第四，《邮差》。第三，《棋子》。第二，《笑忘书》。第一，《暗涌》。王菲最苦的地方，从来不是哭出来，而是把暗伤唱得很轻，轻到多年以后才突然反上来。",
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
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3), "voice": VOICE}
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
