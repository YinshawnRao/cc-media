#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 李宗盛最被低估的5首歌 (countdown 5->1).

Hard rules (see design.md / CONVENTIONS):
- Female voice zf_xiaoyi (brief: 开头/转场/结尾都要女声).
- Intro must NOT reveal the ranking. Outro reveals it (5->1).
- Outro (作品自身) must NOT carry a vote/interaction ask (防双 CTA);
  the fixed CTA (outro_cta) is the very last line, verbatim.
- All song titles are Chinese -> TTS may speak them.
"""
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
    "intro": "提到李宗盛，大多数人先想到的，是《凡人歌》《山丘》这些传唱度最高的大歌。可他真正厉害的地方，是把普通人的人生，一句一句写进歌里。有些歌没有那么高的国民度，藏在专辑深处，却越听越像在说你自己。今天这五首，先不公布完整排名，我们从第五名开始，一首一首慢慢听。",
    # 5 一个人
    "p5_yigeren": "第五名，《一个人》。它收录在一九八六年的《生命中的精灵》里。资料里说，这其实是李宗盛十七岁时写下的作品，很多年以后才正式发表。它没有《寂寞难耐》那样的经典标签，也不像《凡人歌》那样人人会唱，却带着一股蓝调摇滚的冲撞感，写的是一个小城少年的迷茫。作为他创作的一个源头，这首歌特别值得被重新听见。",
    # 4 希望
    "p4_xiwang": "第四名，《希望》。它收录在一九九三年的《希望》这张小专辑里。整张EP其实只有《希望》《如风往事》和伴奏，作品体量很小，所以远不像他那些大歌被反复提起。可它最动人的地方，不是苦情，而是非常朴素的家庭感和生活感——人到了某个阶段才明白，所谓希望不一定是宏大的理想，也可能只是看见孩子眼里的那点光。",
    # 3 远行
    "p3_yuanxing": "第三名，《远行》。它不是李宗盛最典型的中年情歌，而是带着一种离开之前的整理感：想安静下来，把未来重新安排，也想把过去的人和事，慢慢放好。相比后来被反复传唱的那些大歌，它的存在感确实低了很多，可越听越像一封出发前写好的信。",
    # 2 你像个孩子
    "p2_nixiang": "第二名，《你像个孩子》。它同样来自《生命中的精灵》。相比《寂寞难耐》和同名的那首《生命中的精灵》，它没有那么强的代表作标签，却特别能体现李宗盛早期那种半说半唱、像坐在你旁边讲心事的味道。这种直抒胸臆、近乎对白的写法，后来影响了很多华语词作者。",
    # 1 和自己赛跑的人
    "p1_saipao": "第一名，《和自己赛跑的人》。它不是李宗盛最路人化的情歌，也没有《凡人歌》《鬼迷心窍》那种全民辨识度，却最能代表他的人生叙事。它唱的不是爱情，而是一个人怎么跟自己较劲，怎么慢慢变成自己想成为的样子。年轻时听，可能觉得有点说教，过了几年再回头，才发现这首歌很狠——真正难赢的，从来不是别人，是你自己。",
    # 作品 outro：揭晓排名 + 升华，绝不带投票问句
    "outro": "好了，这就是这一期，李宗盛最被低估的五首歌。第五，《一个人》；第四，《希望》；第三，《远行》；第二，《你像个孩子》；第一，《和自己赛跑的人》。李宗盛最厉害的，从来不是写出多少传唱度最高的大歌，而是他把普通人最难开口的那些心事，写得那么准，那么轻。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改。
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
