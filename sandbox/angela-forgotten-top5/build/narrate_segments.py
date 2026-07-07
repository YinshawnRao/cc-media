#!/usr/bin/env python3
"""Generate narration wavs for 张韶涵自己都忘了的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序（倒数）：05《伤日快乐》→ 04《念念》→ 03《绝不》→ 02《控制不了》→ 01《瞬间移动》
BLOCKS = {
    "intro": "张韶涵的代表作，强到会把她自己的其他歌都盖住。《隐形的翅膀》《欧若拉》太会发光，光芒之外，其实还有不少好歌。今天这五首，是连她自己，可能都快忘了的歌。",
    "p5_shangri": "第五名，《伤日快乐》。二零一一年，偶像剧《幸福最晴天》的片尾曲，她自己也在剧里演。它不是当年没存在感，只是时间把热度慢慢冲淡了——张韶涵的剧歌太多，随便拎一首《遗失的美好》出来，都像降维打击。",
    "p4_niannian": "第四名，《念念》。它其实没那么失踪，这些年的舞台上，她还把它重新拿出来唱过。可它始终是一首粉丝向的情歌——旋律很好听，舞台也有，却没能变成一个破圈的名场面。她可能没忘，但路人基本没存档。",
    "p3_juebu": "第三名，《绝不》。二零零七年，它当过《爱杀十七》的插曲，也做过节目的主题曲，口号喊得很用力。可张韶涵早期的剧歌实在太多，《遗失的美好》《寓言》《口袋的天空》全排在前面，《绝不》就这样，被时代的音响盖了过去。",
    "p2_kongzhi": "第二名，《控制不了》。一首二零零七年的快歌，当年甚至拍了正式的MV。它的问题不是没资源，而是定位太边缘——她的快歌，早被《欧若拉》《潘朵拉》《不痛》占满了。老粉听到前奏会想起来，路人听完只会问一句，她还唱过这个？",
    "p1_shunjian": "第一名，《瞬间移动》。二零一零年的个人单曲，励志、奔跑、突破极限，其实非常张韶涵。可偏偏，《隐形的翅膀》《看得最远的地方》已经把这条赛道占满了。歌名很会跑，热度却没跟上，它像是跑进了另一个平行宇宙，连她自己，都快把它弄丢了。",
    "outro": "第五，《伤日快乐》；第四，《念念》；第三，《绝不》；第二，《控制不了》；第一，《瞬间移动》。不是这五首不够好，而是张韶涵的金曲，太会发光了。强光底下，这几首被她自己照淡的歌，其实一直都在。",
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
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3), "voice": VOICE}
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
