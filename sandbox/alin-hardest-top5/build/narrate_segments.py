#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)。输出 audio/<key>.wav + narration.json。

口播里用“阿林”代替 A-Lin，避免中文 TTS 发错音。
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
    "intro": "黄丽玲，阿林最难唱的五首歌，不是只看高音。她难的是大嗓子里还要有细节，爆发里还要有控制。今天从第五名倒数到第一名，越往后，越考验底子。",
    "p5_guilty": "第五名，《失恋无罪》。这是阿林早期招牌歌，难点很直接：强声压，厚声线，和清楚咬字同时来。副歌要唱得痛快，但不能硬吼；情绪要爆，气息却不能散。它不是最高的那首，却很吃基本功。",
    "p4_sorrow": "第四名，《有一种悲伤》。这首不是最炸，却非常难稳。它靠克制，不靠炫技。哭腔不能太满，声音也不能太平，要把悲伤压在声线里慢慢放出来。越到后面，越需要支撑。",
    "p3_happiness": "第三名，《幸福了 然后呢》。这首歌难在综合。它不是一上来就爆，而是从压抑，迷惑，质问，一层一层往上堆。长句，转折，编曲层次都在推情绪；唱早了太满，唱晚了又接不住。",
    "p2_tian": "第二名，《天若有情》。它的难是一个字，大。影视主题曲式的开阔旋律，句子拉得长，气口不能乱，声音还要撑住古装剧那种宿命感。唱这首最怕只剩用力，没有画面。",
    "p1_reason": "第一名，《给我一个理由忘记》。这首是典型的阿林大嗓情歌难度：副歌高位持续，长句很多，情绪一路往上推，但不能只靠喊。唱轻了没爆发，唱重了又失控。K歌很红，真唱很难。",
    "outro": "从第五到第一，《失恋无罪》，《有一种悲伤》，《幸福了 然后呢》，《天若有情》，到《给我一个理由忘记》。阿林最难的地方，不只是嗓门大，而是每一次爆发，都还留着情绪和控制。",
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
