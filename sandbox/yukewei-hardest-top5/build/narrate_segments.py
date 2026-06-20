#!/usr/bin/env python3
"""Generate female narration wavs for the Yisa Yu hardest top 5 video."""
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
    "intro": "郁可唯最难的歌，难点不只在高音。她真正厉害的地方，是把气息、咬字、分寸和人生感都藏在声音里。今天这五首，我们按难度从第五名倒数到第一名，听她怎么把克制唱成重量。",
    "p5_shijianzhuyu": "第五名，《时间煮雨》。这首看似简单，其实很容易唱平。旋律不算炸，但气息一定要干净，线条一定要稳。哭得太满会腻，唱得太白又没故事。难的是那种青春回望的酸，像时间慢慢过去，声音不能脏。",
    "p4_simu": "第四名，《思慕》。这首来自《三生三世十里桃花》，难在长线条和古风咬字。它不能唱得太现代，也不能太戏腔。气口要藏好，情绪要慢慢铺开，有宿命感，但不能像在用力营业。",
    "p3_zhifou": "第三名，《知否知否》。这首难在古风韵味和合唱分寸。它不能唱成普通流行情歌，要有词牌感和留白感；同时还要托住胡夏的低稳声线，不能抢，也不能虚。越淡，越考验控制。",
    "p2_zhiwang": "第二名，《指望》。这是早期郁可唯很典型的高难情歌。副歌位置高，句子长，情绪还要爆发。唱轻了没有委屈，唱重了又容易变硬。真正难的是支撑要够，声音还要像受了伤一样软。",
    "p1_luguorenjian": "第一名，《路过人间》。它的难不是炸，而是克制到极致。每一句都要像在讲一个人的人生，但不能唱得太用力。主歌要轻，副歌要撑，声音里要有阅尽人间之后的温柔、疲惫和不说破。",
    "outro": "所以这期的第一，不给最炫的高音，而给最难拿捏的表达。郁可唯最厉害的地方，是她能把影视歌唱得像人生经过：轻轻开口，却让情绪自己落下来。",
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
