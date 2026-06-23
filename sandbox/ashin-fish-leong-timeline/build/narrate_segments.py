#!/usr/bin/env python3
"""女性旁白：阿信写进梁静茹歌里的另一条五月天时间线。"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline


VOICE = "zf_xiaoyi"
SR = 24000
SPEED = 1.02

BLOCKS = {
    "intro": (
        "很多人都知道，梁静茹是情歌天后。也很多人知道，阿信写歌很会写青春。"
        "但你可能没认真听过，阿信写进梁静茹歌里的，其实是另一条五月天时间线。"
        "阿信为梁静茹写过的歌，按时间顺序听一遍。"
    ),
    "s1_voice": (
        "1999年，第一首是《彩虹》。梁静茹刚刚出道，阿信写给她的，不是后来那种热血，也不是呐喊。"
        "它更像一种潮湿的失落，轻轻落在清晨的窗边。五月天的青春感第一次进入梁静茹的情歌世界时，竟然这么轻，也这么痛。"
    ),
    "s2_voice": (
        "2003年，《Beautiful》。这首不是苦情歌，而是梁静茹开始走向更明亮的女性叙事。"
        "阿信在这里没有写摇滚宣言，他写的是自我确认：一个女生慢慢变漂亮，不只是因为被爱，也因为她终于看见自己。"
    ),
    "s3_voice": (
        "同一年，还有《听不到》。这是阿信很典型的写法：明明很痛，却不哭喊。"
        "梁静茹唱出来之后，痛感被压低了，反而更狠。五月天粉会听到青春失语，梁静茹粉会听到那种委屈但不失态。"
    ),
    "s4_voice": (
        "2004年，《燕尾蝶》是整期第一个爆点。梁静茹不再只是温柔情歌的代表，她开始唱破蛹、扑火和决心。"
        "阿信给她写的不是普通情歌，更像一则摇滚寓言：一个会受伤的人，终于变成一个敢选择的人。"
    ),
    "s5_voice": (
        "同一张专辑里的《纯真》，要特别说明：它不是阿信专门为梁静茹新写的歌，而是五月天旧作被她重新演绎。"
        "五月天唱它，像少年回头看乌托邦；梁静茹唱它，像成年人终于承认，有些东西真的回不去了。"
    ),
    "s6_voice": (
        "2005年，《丝路》。这首歌是梁静茹大歌气质的重要节点。阿信把爱情写成远行，王力宏把旋律做成辽阔的路。"
        "到了梁静茹这里，它变成一场没有终点的追逐，风很大，路很长，但她的声音一直往前。"
    ),
    "s7_voice": (
        "2006年，最后放《可乐戒指》。结尾不需要太沉重，阿信把宏大的爱情重新放回日常。"
        "不用丝路，不用燕尾蝶，一枚可乐拉环也可以是戒指。从抱不住风，到握住一个小小承诺，这条线终于落地了。"
    ),
    "outro": (
        "听完这一遍你会发现，阿信写给梁静茹的不是几首单曲，而是一条很完整的情绪路径。"
        "从抱不住风，到握住一枚可乐戒指，梁静茹把阿信的青春感，唱成了女生自己的成长史。"
    ),
    "cta": (
        "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。"
    ),
}


def main():
    Path("audio").mkdir(exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = Path("audio") / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3), "voice": VOICE, "speed": SPEED}
        print(f"{key:10s} {meta[key]['dur']:6.2f}s")

    Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
