#!/usr/bin/env python3
"""Generate female narration wavs for the Kelly Chen (陈慧琳) hardest top 5 video."""
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

# 倒数盘点：开头不剧透排名，从第五名往第一名听，片尾再一次性列出排名。
BLOCKS = {
    "intro": "提到陈慧琳，很多人先想到的是电音舞曲女王。可她那些听起来轻快好唱的快歌，其实最难。难的不是飙高音，而是要在又快又密的节奏里，把气息、律动、咬字和舞台状态全都同时稳住。这一期我们不先公布完整排名，从第五名开始，一首一首往上听，最后再揭晓。",
    "p5_shuiyuan": "第五名，《谁愿放手》。前面会有一连串快歌，这一首先用慢歌打底。它没有炫技的高音，难就难在控制：每一句都要唱得很稳，把那种遗憾和不舍唱出来，又不能哭腔太重。粤语的尾音、长线条，还有真假声边缘的转换，每一处都很吃功力。",
    "p4_darizi": "第四名，《大日子》。这是典型的陈慧琳式快歌：明亮、利落、节奏感很强，听上去一片喜庆。可现场要唱稳并不轻松，你得唱出那种开心的大场面，但不能靠喊，气息要一直往前推着走，副歌还得有撑得起全场的感染力。",
    "p3_buru": "第三名，《不如跳舞》。林夕填词、雷颂德作曲，是国语舞曲里最容易被低估的难唱歌。它难不在嗓门，而在节奏感：要唱得轻、准、稳，还要有那种别想太多、先跳了再说的松弛。唱太用力就土，不够劲又撑不起整首歌，这个分寸最难拿捏。",
    "p2_shiyi": "第二名，《失忆周末》。这首唱起来比听起来难得多。它的节奏特别密，咬字很碎，气口又窄，现场还要边唱边跳，基本就是一场肺活量的年终考核。它不能拖，一拖就没了俏皮劲；可太赶，又会变成念歌词，整首歌都在走这条钢丝。",
    "p1_huahua": "第一名，《花花宇宙》。这首几乎就是陈慧琳舞曲女王的代名词。它要在电音的快节奏里，把气息、律动和舞台状态全程顶住：副歌要有冲击力，声音却不能发硬；节奏要轻快，气口却不能乱。能把这一首边跳边唱、还唱得稳的，真的没几个人。",
    "outro": "最后总结这一期的排名：第五，《谁愿放手》；第四，《大日子》；第三，《不如跳舞》；第二，《失忆周末》；第一，《花花宇宙》。陈慧琳的难，从来不在高音有多高，而是在又快又密的节奏里，把气息、律动和控制稳稳地唱住，这才是舞曲女王真正的功力。",
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
