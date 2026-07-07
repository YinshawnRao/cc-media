#!/usr/bin/env python3
"""Generate narration wavs for 萧敬腾最难的5首歌."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 揭晓顺序：05《只能想念你》→ 04《白蛇传》→ 03《怎么说我不爱你》→ 02《王妃》→ 01《王子的新衣》
BLOCKS = {
    "intro": "萧敬腾的难，从来不是炫技。是把摇滚的炸，和情歌的痛，唱到一个普通歌手根本撑不住的位置。今天这五首，是萧敬腾最难唱的歌。",
    "p5_zhinengxiangnian": "第五名，《只能想念你》。它不是萧敬腾最炸的那一类，却最吃气息。整首歌不能一上来就用满力，得从压着的隐忍，一点点推到情绪的出口。副歌要有力量，又不能变成硬挤。最难的，是把想念和崩溃之间那段距离，唱得足够长。",
    "p4_baishechuan": "第四名，《白蛇传》。这是萧敬腾第一次当制作人、自己写的歌。它不是普通情歌，而是一出戏，有东方的故事感，有角色，也有冲突。难在你得唱出场景和人物，声音既要爆发，又要有叙事的层次。唱不好，像在用力讲故事；唱好了，才像真的撑起了一台戏。",
    "p3_zenmeshuo": "第三名，《怎么说我不爱你》，收录在《狂想曲》里。它难在大情歌的长线条，前面要压住，副歌一下打开，尾段还得一直撑着那口气。唱太平没有痛感，唱太满又会腻。真正难的，是把那句明明还爱、却说不出口的拉扯，唱到位。",
    "p2_wangfei": "第二名，《王妃》。这是萧敬腾摇滚爆发力最典型的一首。难点在持续的高音、嘶吼的质感，和整个舞台的气场。副歌不是喊上去就行，还要有厚度、有颗粒感、有稳稳的支撑。唱轻了，没有那股王者气；唱重了，又变成硬吼。它考验的，正是一个现场歌手最核心的东西：高、炸、稳，还得有压迫感。",
    "p1_wangzidexinyi": "第一名，《王子的新衣》。它必须排第一。它难的不只是高音，而是那种美式抒情摇滚的高压。副歌要顶住极强的声压，声音得穿过整支乐队，还要把节奏和咬字咬得清清楚楚。整首歌的情绪是疯的、是危险的，唱太规矩没戏，唱太放又会失控。最难的，是把爆发唱得有控制，把那股疯劲，唱得有准度。",
    "outro": "完整榜单。第五，《只能想念你》。第四，《白蛇传》。第三，《怎么说我不爱你》。第二，《王妃》。第一，《王子的新衣》。萧敬腾最难的歌，难就难在他从不只靠嗓门。他能把炸和稳放在一起，把疯和准放在一起，让你真正听见，什么叫现场。",
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
        print(f"{key:22s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
