#!/usr/bin/env python3
"""Female narration wavs for 飞儿乐队最被低估的5首歌."""
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
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "提到飞儿乐团，很多人会先想到《Lydia》《我们的爱》《月牙湾》这些大歌。但 F.I.R. 最迷人的部分，不只是高音和副歌爆点，而是那种早期华语乐坛少见的冒险感、信念感，还有一点奇幻摇滚的世界观。这一期，我们按排名倒数，听五首被低估的飞儿遗珠。",
    "p5_juanlian": "第五名，《眷恋》。它来自《爱·歌姬》。这张专辑的记忆点几乎都被《月牙湾》占住，旁边还有《需要你的爱》《三个心愿》这些更容易被提起的歌。《眷恋》反而像藏在后面的慢热情歌。它的伤感很克制，不急着催泪，只把那种把爱埋进记忆里的痛，慢慢唱出来。",
    "p4_tiantiianye": "第四名，《天天夜夜》。放在《飞行部落》里，它确实没有《北极圈》《雨樱花》那么容易被立刻想起。但这首有一种很纯粹的旋律美。它不是飞儿最炸裂的摇滚路线，而是更柔软、更夜色感的一面。老粉夜里重听，往往会突然发现，这首怎么当年没有被更多人听见。",
    "p3_houleyuan": "第三名，《后乐园》。首张同名专辑实在太能打，《Lydia》《我们的爱》《你的微笑》《Fly Away》几乎把大众记忆全部占满。《后乐园》就显得低调。可它很能代表 F.I.R. 早期的奇幻摇滚审美，旋律不算最路人，氛围却很完整，像他们音乐宇宙里一个被忽略的入口。",
    "p2_baaifangkai": "第二名，《把爱放开》。它也是《无限》里的遗珠，长度超过五分钟，情绪铺得很开，不靠一句副歌马上抓人，而是把放手的痛感一点点推起来。同专辑有《千年之恋》《Love Love Love》《无限》这些更醒目的名字，所以这首更像真爱粉会单独捡出来听的慢热大歌。",
    "p1_yingxuzhidi": "第一名，《应许之地》。这首特别有飞儿早期那种史诗感、摇滚感和信念感。它不是第一耳爆款，却越听越能听见 F.I.R. 最核心的世界观：他们不只是唱爱情，也唱冒险、信仰和远方。在《无限》这张强专辑里，它像藏在中段的一座城，没被所有人看见，但分量非常重。",
    "outro": "最后再把榜单收一下。第五，《眷恋》；第四，《天天夜夜》；第三，《后乐园》；第二，《把爱放开》；第一，《应许之地》。飞儿乐团真正被低估的，是他们把流行旋律、摇滚能量和奇幻叙事揉在一起的能力。那些不是最大热的歌，反而最能听见他们的野心。",
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
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
