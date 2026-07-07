#!/usr/bin/env python3
"""Male narration for 张艺兴最难的5首歌.

Countdown 5 -> 1（按用户给定难度排名，#1=莲 为压轴最难）。
事实口径（WebSearch 交叉核实，见 SOURCES.md）：
- 莲 = 2020 单曲。
- 飞天 = 2021-10-15，收录 EP《东/EAST》。
- 梦不落雨林/NAMANANA = 2018-10-19，张艺兴第三张个人专辑同名主打曲，本人独立作曲编曲。
- 面纱 = 2022-09-21 单曲。
- 酒(JIU) = 2022-04-08，出道十周年纪念单曲。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句；作品自身 outro 不再自带投票问句。
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
    "intro": "张艺兴，唱跳全能，是公认的实力派。但他的歌单里，藏着几首连他自己都不敢轻易挑战的作品：说唱、舞台、气息、情绪，样样都要顶到极限。今天倒数盘点，张艺兴最难的五首歌，从第五名开始。",
    "p5_jiu": "第五名，《酒》。它不是最炸的张艺兴，却最考验松弛感。歌名听着轻松，唱起来却要带一点微醺感、一点转音的弹性，太规矩就没了酒意，太散又会不稳。作为难度榜的起点，它藏着张艺兴作品里更细腻、更氛围化的一面。",
    "p4_mianshan": "第四名，《面纱》。它偏电子氛围质感，难点在暧昧、在真假声的边缘，还有节奏的精准。它不像后面几首靠大场面压场，而是吃细节：气声要稳，咬字要松，情绪还要留一点神秘感。唱太实丢了性感，唱太虚又没了支撑。",
    "p3_menglin": "第三名，《梦不落雨林》，收在他自己作曲编曲的第三张专辑里。整首歌节奏密、律动强，中英双版本更让咬字和处理变得复杂。它不靠大高音取胜，靠的是groove、气息的弹性和舞台的流动感。唱太直没味道，太松又掉拍，身体的律动，一秒都不能停。",
    "p2_feitian": "第二名，《飞天》。它有官方练习室版本，说明这不是一首站桩型的歌，而是彻头彻尾的舞台型作品。唱它要有轻盈感，也要有力量感，动作一多气息就容易散，声音太轻又撑不起那种敦煌般的开阔和神话感。这考验的，是唱跳歌手的综合能力。",
    "p1_lian": "第一名，《莲》。它把唱跳、国风、说唱、强节奏和舞台气场，全部叠在了一起。副歌要有冲击力，rap段要咬字清楚，舞蹈动作又极重，气息稍微一乱，整首歌的压迫感就会塌。这不是传统意义上的飙高音难歌，而是张艺兴式的高难：节奏要狠，动作要稳，声音还要撑住最大的场面。",
    "outro": "五首歌盘完。第五《酒》，第四《面纱》，第三《梦不落雨林》，第二《飞天》，第一《莲》。张艺兴的难，从来不只是唱得多高，而是唱跳说唱舞台全部叠加时，声音还能不能稳得住。这五首歌，刚好拼出了他作为唱跳歌手最完整的实力版图。",
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
