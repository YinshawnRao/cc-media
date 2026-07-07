#!/usr/bin/env python3
"""Male Mandarin narration wavs for 陈慧琳最被低估的5首歌."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "提到陈慧琳，很多人会先想到《不如跳舞》《花花宇宙》《记事本》《失忆周末》。但她的作品里，还有一批没被推到代表作位置的都市情歌。它们不靠大开大合，而是把克制、距离、夜色和成年人关系里的无力感，唱得很细。这一期，我们按排名倒数，听五首陈慧琳最被低估的歌。",
    "p5_peiwo": "第五名，《陪我失眠》。它来自《爱情来了》。这首不是轰轰烈烈的痛，而是夜里睡不着的时候，希望有人陪你一起熬过情绪。旋律没有特别夸张的爆点，但氛围很完整，带着夜色感、陪伴感，也有一点孤单。",
    "p4_chubudao": "第四名，《触不到的恋人》。它的好，是那种明明靠近，却始终隔着距离的遗憾。不是热烈告白，也不是彻底失恋，而是关系里若即若离的酸。陈慧琳唱这种有距离的情歌，声音越清，越显得冷。",
    "p3_xiangxun": "第三名，《香薰恋爱治疗》。在《花花宇宙》那张专辑里，《花花宇宙》和《失忆周末》太强，几乎把大众记忆都带到了跳舞女王那一面。这首慢板情歌反而像藏在热闹背后，轻轻说一个人试着修复感情里的疲惫。",
    "p2_wenrou": "第二名，《温柔眼泪》。它来自《心口不一》，是一首很容易被低估的慢歌。温柔和眼泪，两个看似相反的词放在一起，情绪就不是撕裂式的痛，而是很轻、很软、很克制地难过。陈慧琳在这里唱得稳，也很耐听。",
    "p1_fangbu": "第一名，《放不开手》。同一张《心口不一》里，有《我要的只是爱》《是我不好》《心口不一》这些更容易被记住的歌，所以它很容易被盖住。但这首最能听见她国语慢歌里成熟的一面：舍不得、放不下，又知道该放手，越听越有成年人关系里的无力感。",
    "outro": "最后再把榜单收一下。第五，《陪我失眠》；第四，《触不到的恋人》；第三，《香薰恋爱治疗》；第二，《温柔眼泪》；第一，《放不开手》。陈慧琳被低估的，不只是某几首歌，而是她把都市情绪唱得清亮、克制，又不失温度的能力。",
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
    (ROOT / "narration.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
