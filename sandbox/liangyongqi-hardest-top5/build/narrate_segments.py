#!/usr/bin/env python3
"""Generate female narration wavs for the Gigi Leung (梁咏琪) hardest top 5 video."""
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
    "intro": "梁咏琪，高妹，一把清亮又干净的声音。但今天我们不聊她有多美，只聊一件事——她的歌，到底有多难唱。这五首，有粤语的咬字，有气息的控制，还有那种唱崩了就垮、唱稳了才动人的分寸。先不排名，我们从第五名开始。",
    "p5_gaomei": "第五名，《高妹正传》。它是专辑《Funny Face》的第一主打，梁咏琪自己作曲，黄伟文填词。它难，不在高音，而在那股看起来轻松的劲儿——节奏、咬字，还有现场的灵动感，都得拿捏。唱得俏皮、自信、不费力，才算难；一用力就笨，一太轻，又没了态度。",
    "p4_xianqi": "第四名，《嫌弃》。它收录在专辑《G For Girl》里。这首适合放进难唱榜，不是因为多高，而是因为情绪很拧、很别扭。粤语咬字要清楚，情绪要有锋利感，却又不能唱成苦情的嘶吼。听起来不算神曲，真唱起来，最容易暴露一个人的控制力。",
    "p3_yanwu": "第三名，《烟雾弥漫》。它比很多人想象中难。难点，在虚和实的切换：前面要有一层烟雾感，不能唱得太满；副歌又要撑住那条旋律线，不能一虚到底。在现场唱它，最吃气息和音准的稳定，一个不稳，整段就散了。",
    "p2_huahuo": "第二名，《花火》。它是梁咏琪粤语歌里很典型的高难度作品。它不走大嗓门，而是要把明亮、脆弱、还有那一点希望感，一起唱出来。副歌既要有飞起来的感觉，又不能唱薄。这种清亮的声线，最能体现她的特质，也最不容易唱稳。",
    "p1_yuanlai": "第一名，《原来爱情这么伤》。它难在副歌一路走高，情绪层层递进，却不能只靠喊。声音要一直保持干净、明亮、稳定，还要唱出失恋之后那种崩塌感。整首歌唱到尾声，像是和自己打完了一场仗——这种歌，最怕情绪到了，声音却先阵亡。",
    "outro": "再回顾一次这份榜单：第五，《高妹正传》；第四，《嫌弃》；第三，《烟雾弥漫》；第二，《花火》；第一，《原来爱情这么伤》。梁咏琪的难，从来不是炫技的高音，而是那把清亮的声音，要在轻巧里有态度，在脆弱里有力量，把每一分控制，都藏进听起来很轻松的旋律里。",
    "outro_cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
