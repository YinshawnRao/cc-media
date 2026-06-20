#!/usr/bin/env python3
"""Generate female narration wavs for the Joey Yung (容祖儿) hardest top 5 video."""
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
    "intro": "容祖儿最难唱的歌，难的往往不是那几个高音，而是情绪。她要在很拧、很克制的旋律里，把痛唱得有重量，又不能崩成苦情戏。今天这五首，不先公布完整排名，我们从第五名开始，一首一首听，她到底难在哪里。",
    "p5_tongai": "第五名，《痛爱》。这是容祖儿早期的广东歌代表作，拿过不少重要的歌曲奖。它不是最高、最炸的一首，难就难在情绪控制和音色质感。你不能只唱一个痛字，要唱出一种已经知道自己输了、却还放不下的克制。太平静没有故事，太用力又会变俗。",
    "p4_airen": "第四名，《十六号爱人》。它常被当成一首K歌苦情歌，其实很难唱好。副歌要有受伤之后的不甘，但又不能唱得太怨；声音要有支撑，还要保留女生视角里那份脆弱。它当年不是主打歌，后来却意外大热，成了KTV里的热唱曲。这种歌最可怕：人人都会哼，但真正唱稳的没几个。",
    "p3_soushen": "第三名，《搜神记》。它难在密，也难在稳。林夕的词信息量很大，曲子又不是顺口的口水旋律，很多句要在很窄的气口里，把字咬清楚，还要唱出从失恋到自我打开的那股气势。它不是炫技型，但特别考验咬字、节奏，和情绪一层一层的递进。",
    "p2_xindan": "第二名，《心淡》。这是容祖儿的经典难歌。它看起来像首大众情歌，可副歌的连续推进，非常吃气息和稳定性。唱轻了，没有那种心死的重量；唱重了，又容易变成硬喊。黄伟文的词本来就密，旋律一直把情绪往上推，所以它不是一两个高音难，而是整首都要稳住。",
    "p1_poxiang": "第一名，《破相》。它的难，在于整首歌情绪很拧，旋律线又不允许你随便哭腔乱飘。主歌要压住，副歌要打开，可打开之后，还得保持锋利和体面。陈辉阳的曲，黄伟文的词，本身就是旋律有戏、歌词带刀的配置。普通人来唱，很容易只剩下苦，唱不出那份美。",
    "outro": "最后总结这期排名。第五《痛爱》，第四《十六号爱人》，第三《搜神记》，第二《心淡》，第一《破相》。容祖儿的难，从来不是飙得有多高，而是能不能把那么拧、那么痛的情绪，唱得既锋利，又体面。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（见 tools/video/outro_cta.py / CONVENTIONS「固定结尾配音」）。
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
        print(f"{key:12s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
