#!/usr/bin/env python3
"""Generate female narration wavs for the Na Ying hardest top 5 video."""
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
    "intro": "那英最难唱的歌，不只是比谁音高，也不是嗓门越大越难。真正考验的是厚度、穿透力、气息、咬字和情绪爆发能不能同时顶住。这期不先公开完整榜单，我们从第五名往第一名听，最后再一次性总结排名。",
    "p5_buguan": "第五名，《不管有多苦》。这首难在强情绪和强机能同时存在。它不是慢慢铺开，而是更直接、更硬朗，中高区支撑和气息耐力都要一直在线。越唱到后面越像体能测试，声音一松，那股倔劲就撑不住了。",
    "p4_chumai": "第四名，《出卖》。这首是那英情歌里很考控制力的一首。旋律一直在情绪高压区游走，副歌不能太轻，也不能太狠；唱轻了没有痛感，唱重了又容易变成硬吼。最难的是把背叛感唱出来，但声音还要稳、准、收得住。",
    "p3_baitian": "第三名，《白天不懂夜的黑》。这首难在高位强声和持续咬字。副歌旋律很开，情绪很大，声音既要厚，又要亮，还不能唱得笨重。它不是细腻型难歌，而是大开大合的考验：气息、胸声支撑、强混和音准都要在线。",
    "p2_mo": "第二名，《默》。这首是听起来克制，唱起来很险。前面要压住情绪，声音不能太满；后面副歌一层一层推上去，高位要稳，气息要长，情绪还要越来越深。难点不是单个高音，而是从低压一路推到爆发，声音不能散，情绪也不能假。",
    "p1_zhengfu": "第一名，《征服》。这首基本就是那英声乐难度的代表作。主歌要稳、要厚，副歌突然打开以后，高位强声和情绪爆发都要同时顶住。最难的是不能只靠喊，声音要有力量、有穿透力，还要保留那英那种沙哑里的亮度。普通人唱这首，很容易前面还在征服，后面已经被嗓子征服。",
    "outro": "最后总结这期排名。第五《不管有多苦》，第四《出卖》，第三《白天不懂夜的黑》，第二《默》，第一《征服》。那英的难，不只是嗓子够不够大，而是力量、沙哑、亮度和情绪能不能在同一个高压点上稳住。",
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
        print(f"{key:12s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
