#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)。输出 audio/<key>.wav + narration.json。

最后一段 fixed outro_cta 是全系列固定 CTA，必须排在作品 outro 之后。
"""
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
SPEED = 1.04
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "王菲最难的五首歌，这一期不只看高音。我们看的是音准、气息、共鸣、律动，还有那种轻到快要消失，却又稳稳落地的控制力。从第五名倒数到第一名，越往后，越不是普通人靠模仿能解决的难。",
    "p5_kaidao": "第五名，《开到荼蘼》。这首难的不是大嗓门炸场，而是在冷、倔、锋利之间保持平衡。主歌要有态度，但不能散；副歌要有推力，但不能吼。最难的是，你要有锋芒，却不能显得你很努力。",
    "p4_bianhua": "第四名，《彼岸花》。它和《寒武纪》一样属于《寓言》的前卫五部曲，但难点更像长线条的悬浮。整首歌要一直空、远、宿命，气息不能断，尾音不能脏，声音也不能太实。越轻，越难有支点。",
    "p3_hanwuji": "第三名，《寒武纪》。它不是传统意义上的高难度炫技歌，可非常难唱对。主歌像漂在空气里，副歌又要撑住叙事感；不能哭，不能喊，不能太戏剧化。唱少了像没情绪，唱多了又破坏那种冰冷的寓言感。",
    "p2_duodeta": "第二名，《多得他》。这首是王菲早期 R and B 唱法里很难的一面。难点在转音、律动、咬字和情绪收放。它不是把旋律唱准就行，每一句都要有 groove，声音要轻盈但不能薄，转音自然但不能油。",
    "p1_face": "第一名，《脸》。这首难的不是高音，而是腔体和控制。它接近类美声的圆、厚、立体，却又不能唱成学院派；还要保留王菲那种轻、冷、飘。音准、气息、共鸣位置和尾音都要干净，稍微用力就俗，稍微虚一点又会塌。",
    "outro": "所以这份榜单，从《开到荼蘼》的锋利，到《彼岸花》和《寒武纪》的悬浮，再到《多得他》的律动，最后落在《脸》的腔体控制。王菲最难的地方，是她看起来很轻，其实每一个音都站得很稳。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        sf.write(AUDIO / f"{key}.wav", audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:14s} {meta[key]['dur']:6.2f}s")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
