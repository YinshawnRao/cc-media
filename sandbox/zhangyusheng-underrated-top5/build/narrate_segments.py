#!/usr/bin/env python3
"""Male narration for 张雨生最被低估的5首歌.

Countdown 5 -> 1 (#1 = 河, the climax). Years on screen corrected vs brief:
《还是朋友》= 1995, 《一天到晚游泳的鱼》= 1993. The final CTA is imported from
tools/video/outro_cta.py (repo-level convention, always the last spoken line).
专辑英文名/外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
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
    "intro": "提到张雨生，很多人先想到的，是那个唱《我的未来不是梦》的明亮嗓音，是能把《大海》飙到云端的高音。可他真正的分量，藏在那些没被传唱烂的歌里。他从来不只是会唱高音，他是个有格局、有野心的创作者。今天这期，我们从第五名倒数，盘一盘张雨生最被低估的五首歌。",
    "p5_ziyou": "第五名，《永远的自由》。它收在一九九五年的《还是朋友》里，没有那些大热作品的传唱光环，却特别能代表张雨生这个人。他在意的，从来不只是把音唱多高，而是自由、理想，还有对生命本身的好奇。这首歌很明亮，却一点都不天真，唱的是一个少年对世界的向往和追问。听它，你会想起张雨生身上那股一直没被磨掉的赤诚。",
    "p4_meimei": "第四名，《妹妹晚安》。它来自一九九三年的《一天到晚游泳的鱼》。同张专辑里，标题曲太亮眼，把这首温柔的小歌整个盖了过去。它没有宏大的叙事，也不是高亢的宣言，更像睡前轻轻的一句道别和守护。张雨生唱这种日常里的温柔，特别干净，也特别真，能听见他声音里很少示人的那一面。",
    "p3_fengzheng": "第三名，《我是风筝》。它和《永远的自由》一样，收在《还是朋友》里，更像藏在专辑中段的一颗遗珠。歌名就很张雨生，有飞翔的自由，也有被一根线牵住的无奈。它唱的不是简单的离别，而是那种想挣脱、又被命运拉住的状态。张雨生的声音很亮，可情绪一点都不轻，越听，越能听见那股藏在明亮底下的孤独。",
    "p2_miaoxiao": "第二名，《渺小》。它来自一九八八年的《天天想你》，比起同名主打和《我的未来不是梦》，存在感弱了太多。可这首歌很重要，它的歌词取自徐志摩的新诗，写的是人站在天地、山川和时间面前的那种渺小与感怀。它不是普通的青春情歌，而是早早就显露出，张雨生后来作品里那种人文关怀和大视野。年轻时听觉得遥远，长大了再听，才发现它有多重。",
    "p1_he": "第一名，《河》。它收在一九九七年的《口是心非》里，同张专辑有《口是心非》这种大众记忆更强的作品，很容易把它盖住。可《河》最能代表张雨生后期的野心，它不是常规的流行情歌，从温柔的钢琴和弦乐起笔，又突然转进一段气势磅礴的电吉他，曲式大胆得不像那个年代的华语歌。它不是第一耳朵就抓人的爆款，却越听，越能听见张雨生作为创作者，真正的格局。",
    "outro": "五首歌盘完。第五，永远的自由；第四，妹妹晚安；第三，我是风筝；第二，渺小；第一，河。张雨生从来不只是那个会飙高音的歌手，他是个有大视野的创作者。这些被大热歌盖住的遗珠，刚好补全了他最珍贵、也最被低估的另一面。",
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
