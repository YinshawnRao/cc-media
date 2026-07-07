#!/usr/bin/env python3
"""Generate male narration wavs for 徐良最被低估的5首歌."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zm_yunxi"
SPEED = 1.04
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "有些歌不是不够好听，而是被时代和热歌压住了。提到徐良，很多人会先想到最出圈的合唱和网络记忆。但他真正耐听的地方，常常藏在那些没被反复盘点的歌里。这一期，我们倒着盘五首徐良最被低估的遗珠。",
    "p5_zihuaxiang": "第五名，《自画像》。这首歌的特别之处，是它没有急着讲一个戏剧化故事，而是把镜头转向自己。早期网络情歌很多都在写关系，可《自画像》更像一次自我确认，稚嫩，但很真。",
    "p4_yigongli": "第四名，《一公里的幸福》。它写的不是轰轰烈烈，而是明明只差一点，却怎么也走不到的距离感。旋律很轻，情绪却很旧，像青春里那种回头看才发现的遗憾。",
    "p3_huanmie": "第三名，《幻灭》。它没有把失去写成大哭大闹，而是写成一种慢慢冷下来的清醒。等幻想散掉以后，人才会看见自己一直在骗自己，这种后劲，其实比直接煽情更重。",
    "p2_dianhua": "第二名，《电话里的秘密》。这首歌最动人的不是电话这个道具，而是电话里那些没说完、也不敢说破的话。徐良把沉默写得很具体，让一段关系的距离感，全都藏在声音背后。",
    "p1_beijing": "第一名，《北京巷弄》。它不是那种一秒抓耳的爆款副歌，却是徐良早期作品里画面感很强的一首。巷子、旧人、城市和回忆，都被写得很有生活气，所以越往后听，越觉得它不该被忽略。",
    "outro": "最后把榜单收回来。第五，《自画像》；第四，《一公里的幸福》；第三，《幻灭》；第二，《电话里的秘密》；第一，《北京巷弄》。徐良被低估的，不只是旋律，而是他把青春里的自我凝视、距离感和生活画面，全都写进歌里的能力。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:16s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
