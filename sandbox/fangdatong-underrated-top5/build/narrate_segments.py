#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 方大同最被低估的5首歌 (countdown 5->1).

Hard rules (see design.md):
- Female voice zf_xiaoyi.
- TTS text never pronounces English titles (Take Me / Orange Moon / Over) — Kokoro
  misaki[zh] mangles CN-EN mixing. Voice describes those songs; on-screen card carries
  the exact title. Chinese titles (暖 / 黑洞里) may be spoken.
- Pure-Chinese terms only (灵魂乐 / 律动, never Neo-Soul/R&B/groove inside TTS).
- Intro must NOT reveal the ranking. Outro reveals it (screen lists exact titles).
"""
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
    "intro": "方大同的歌，很多人只记得最传唱的那几首。但真正让乐迷单曲循环的，常常是那些没被做成主打、却全是功夫的遗珠。今天这五首，先不公布完整排名，我们从第五名开始，一首一首听他到底高级在哪里。",
    # 5: 《Over》 — voice does NOT say the title
    "p5_over": "第五名，是一首歌迷越听越懂、路人却很少主动点开的作品。它没有主打的光环，也不靠大副歌煽情，全凭那种灵魂乐的律动，松弛、细腻、耐听。听起来毫不费力，里面却全是功夫。",
    # 4: 《暖》 — voice may say 暖
    "p4_nuan": "第四名，《暖》。在《未来》这张专辑里，它的存在感一直不算强。但这首其实最有方大同那种非典型情歌的气质，它写的不只是爱情，还有关怀、善意和温度。不是第一耳的爆款，却越听越像一束不刺眼的光。",
    # 3: 《黑洞里》 — voice may say 黑洞里
    "p3_heidongli": "第三名，《黑洞里》。它没有《三人游》那么大众，也没有《黑白》那么抓耳，却是《橙月》里很容易被忽略的高级情歌。氛围和律动都很细，像一段慢慢往内心下沉的独白。方大同最厉害的，是把灵魂乐的和声和节奏，自然地放进华语歌里。",
    # 2: 《Orange Moon》 — voice does NOT say the title
    "p2_orangemoon": "第二名，是整张专辑里彩蛋级的遗珠。它藏在《橙月》的最后，也是方大同写给陈奕迅《倒带人生》最早的那版英文雏形。一个人，一把吉他，一轮橙色的月亮，安静得像深夜里只唱给自己听。它没有大热歌的锋芒，却有很强的私人感。",
    # 1: 《Take Me》 — voice does NOT say the title
    "p1_takeme": "第一名，这首歌一上来，吉他和律动就把人整个带起来。它不是方大同最路人的情歌，却最能代表他音乐里的那股爽感。不靠苦情的副歌取胜，而是用节奏和编曲让人跟着摇。放在《15》里，它很容易被《因为你》《好不容易》这些更红的歌盖过，但真爱粉一定懂它的高级。",
    "outro": "这就是这一期，方大同最被低估的五首歌。从第五到第一，它们没有最高的传唱度，却把他的才华藏在最不张扬的地方。方大同最迷人的，从来不只是好听的旋律，而是那份听起来轻松、其实满是功夫的高级。愿你也能在这几首里，重新认识他。",
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
