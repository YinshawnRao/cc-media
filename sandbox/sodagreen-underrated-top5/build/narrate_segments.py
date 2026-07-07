#!/usr/bin/env python3
"""Male narration for 苏打绿最被低估的5首歌.

Countdown 5 -> 1 (#1 = 无言歌, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 频率 = 鼓手史俊威 作词 + 作曲（不是青峰）；最早是他骑车时写的一首诗，后改成歌。苏打绿同名专辑 2005。
- 彼得与狼 = 吴青峰 词曲。歌名借自普罗科菲耶夫交响童话《彼得与狼》。《夏／狂热》2009。
- 包围 = 吴青峰 作词 / 苏打绿（全团）作曲。《夏／狂热》2009。
- 燕窝 = 吴青峰 词曲。曾获第23届金曲奖最佳音乐录影带（MV）提名。《你在烦恼什么》2011。
- 无言歌 = 吴青峰 词曲。歌名取自门德尔松《无言歌》。《小宇宙》2006。
乐团 = 六人，主唱吴青峰。专辑外文名/英文一律不进配音（Kokoro 中英混读差），只进字幕。
《夏／狂热》口播写成《夏，狂热》（避免斜杠被误读），屏幕字幕仍写 夏／狂热。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。
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
    "intro": "提到苏打绿，很多人先想到的，是《小情歌》《无与伦比的美丽》《你被写在我的歌里》这些传唱度最高的歌。可这支六人乐团真正迷人的地方，往往藏在那些没那么红、却被老歌迷反复回听的遗珠里。今天这期，我们从第五名倒数，盘一盘苏打绿最被低估的五首歌。",
    "p5_pinlv": "第五名，《频率》。它来自二零零五年那张苏打绿的同名专辑。和后来那些更成熟、更出圈的大歌相比，《频率》带着很明显的早期青涩，却也藏着一个少有人知的来历——这首歌的词和曲，都不是青峰写的，而是出自鼓手史俊威。最早，它只是他骑车时写下的一首诗，后来才被谱成了歌。也正因为这样，它像一张旧照片，编曲没那么华丽，却能听见这支乐团最初的那份清澈和敏感。",
    "p4_bdwolf": "第四名，《彼得与狼》。它收在二零零九年的《夏，狂热》里。它的被低估，不是因为不好听，而是因为它太不像大家最熟悉的那个苏打绿——不是温柔的情歌，而是一首带着寓言色彩的摇滚。歌名借自普罗科菲耶夫的同名交响童话，歌里有角色、有讽刺，也有青峰少见的那种锋利。它补上了苏打绿的另一面：他们不只会写青春和温柔，也会写权力、写人性的荒诞。",
    "p3_baowei": "第三名，《包围》。它同样来自《夏，狂热》。相比《他夏了夏天》那种更醒目的作品，《包围》更像专辑里一条锋利的暗线。有意思的是，这首歌的词是青峰写的，而曲，是六个人一起完成的。整张《夏，狂热》用摇滚和对现实的观察，写尽了那股夏天的燥热，而《包围》，是其中压迫感最强的一首——它不是温柔小品，而是被现实层层围住之后，还想拼命往外冲的那股劲。",
    "p2_yanwo": "第二名，《燕窝》。它来自二零一一年的《你在烦恼什么》。同张专辑里，《你被写在我的歌里》《当我们一起走过》更容易出圈，《燕窝》反而低调了很多，但它其实拿过金曲奖最佳音乐录影带的提名。这首歌最厉害的地方在于细：像一个人在自己的小空间里，慢慢把情绪一点点整理好。苏打绿很会把日常的小物件，写出生命感，不张扬，却特别温暖，这首，就是最典型的一个。",
    "p1_wuyan": "第一名，《无言歌》。它收在二零零六年的《小宇宙》里，可同张专辑，有《小情歌》这样的国民级大歌，几乎把它整个盖住了。歌名取自门德尔松的《无言歌》。它最能代表苏打绿早期那种戏剧性和诗意——不是靠一个大副歌抓人，而是靠情绪一层一层往上堆，把很多说不出口的话，唱成一种无言的重量。它不算最路人化的苏打绿，却是最让团粉反复回味的那一首。这，才是最被低估的苏打绿。",
    "outro": "五首歌盘完。第五，频率；第四，彼得与狼；第三，包围；第二，燕窝；第一，无言歌。苏打绿从来不只是那个唱青春情歌的乐团，他们也会写社会、写荒诞，写那些说不出口的沉默。这些被大热歌盖住的遗珠，刚好补全了他们最被低估、也最值得被重新听见的另一面。",
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
