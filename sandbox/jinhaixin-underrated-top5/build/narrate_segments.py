#!/usr/bin/env python3
"""Generate female narration wavs for 金海心最被低估的5首歌."""
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
    "intro": "提到金海心，很多人会先想到把耳朵叫醒、那么骄傲，或者阳光下的星星。可她最迷人的地方，不只在这些大热歌里。今天这五首，是被专辑光芒盖住、却很值得重新听的遗珠。我们从第五名开始，慢慢往第一名走。",
    "p5_laibuji": "第五名，《来不及》。它收在《那么骄傲》那张专辑里，可同名主打太强，猫咪森林、把鞋子甩掉也更容易被记住，所以它很容易被路人跳过。但这首歌的遗憾感很耐听，不是大哭大闹，而是慢半拍才意识到失去。它没有爆点，却很像真爱粉会翻出来单曲循环的那一类。",
    "p4_bitian": "第四名，《比天空还远的季节》。这首是《独立日》里的安静遗珠。同一张专辑有阳光下的星星、右手戒指、独立日这些更容易被第一时间记住的歌，它就显得更内向。可它的歌名和气质都很金海心，有空间感，有季节感，也有一点远远的孤独，适合夜里重新听。",
    "p3_duian": "第三名，《对岸》。它来自金海心同名专辑，同张里悲伤的秋千存在感更强，所以这首很容易被忽略。对岸这个名字本身就有画面，两个人像隔着一条河，能看见，却很难真正抵达。金海心的声音自带透明感，唱这种有距离的情绪，不用很用力，反而更有后劲。",
    "p2_sleep": "第二名，《睡不着的海》。这首来自首专《把耳朵叫醒》，当年在专辑推出前就已经被电台和乐评注意到。只是后来大众记忆更多集中在把耳朵叫醒和那么骄傲，它反而像早期宝藏被压在标题曲后面。它的好在氛围，有海、有夜、有不安，不是简单小甜歌。",
    "p1_right": "第一名，《右手戒指》。这首我会放第一。它收录在《独立日》里，同张专辑有阳光下的星星这种更容易出圈的歌，所以右手戒指很容易被盖住。它不是金海心最典型的甜美情歌，而是更有自我解放的气质，旋律明亮，歌词也有童话式的自由感。现在路人很少提它，低估得很明显。",
    "outro": "最后把榜单完整收一次。第五，来不及；第四，比天空还远的季节；第三，对岸；第二，睡不着的海；第一，右手戒指。金海心最被低估的，往往不是唱得不够好，而是太轻、太透、太容易被大热歌盖过去。",
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
