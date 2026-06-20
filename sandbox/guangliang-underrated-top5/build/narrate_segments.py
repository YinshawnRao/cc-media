#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 光良最被低估的5首歌 (countdown 5->1).

Hard rules (see design.md / CONVENTIONS):
- Female voice zf_xiaoyi (brief: 开头/转场/结尾都女声).
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
    "intro": "提到光良，大多数人会先想到《童话》和《第一次》。可他真正动人的好歌，远不止那几首传唱度最高的。有些歌藏在专辑深处，安静、克制，却越听越有后劲。今天这五首，先不公布完整排名，我们从第五名开始，一首一首慢慢听。",
    # 5 住在遥远的星球
    "p5_xingqiu": "第五名，《住在遥远的星球》。它收录在《不会分离》这张专辑里，同张更被记得的，是《烟火》和《不会分离》。这首更像专辑后段的私藏曲。光是歌名就很有画面——不是激烈的失恋，而是两个人明明还在同一个世界，却像隔着很远很远的距离。越安静，越有后劲。",
    # 4 海边
    "p4_haibian": "第四名，《海边》。这是《童话》里的另一首隐藏款，由陈熙作词作曲。它没有《童话》的全民记忆，也没有《少年》的合唱声量，但氛围特别舒服。它不强行煽情，而是把情绪轻轻放进风里、海边和回忆里——是光良温柔情歌里，少见的那种留白。",
    # 3 期限
    "p3_qixian": "第三名，《期限》。《童话》这张专辑实在太能打，同名主打红遍亚洲，还有《天堂》《少年》这些更容易被记住的歌，《期限》就很容易被埋住。可它其实很有专辑深处遗珠的气质——不是第一耳就抓人，但那种时间感和等待感，特别适合老歌迷慢慢回听。",
    # 2 握你的手
    "p2_woni": "第二名，《握你的手》。它很适合放进真爱粉的遗珠歌单。不像《童话》那样大众催泪，也不是《第一次》那种青春纯爱，而是更安静、更细腻的表达。光良的官方资料，也把它和《第一次》《童话》《天堂》一起，列为他展现唱作实力的代表作，只是在路人的歌单里，它的存在感低了太多。",
    # 1 如果你还爱我
    "p1_ruguo": "第一名，《如果你还爱我》。它来自《第一次个人创作专辑》，是光良第一首完整的词曲创作。同张里《第一次》太强，《朋友首日封》也更常被提起，所以这首一直像藏在专辑里的一桩心事。它最动人的，不是狗血的情节，而是那种明明还在等，却已经感觉到对方慢慢变冷的失落。",
    # 作品 outro：揭晓排名 + 升华，绝不带投票问句
    "outro": "好了，这就是这一期，光良最被低估的五首歌。第五，《住在遥远的星球》；第四，《海边》；第三，《期限》；第二，《握你的手》；第一，《如果你还爱我》。光良最打动人的地方，从来不是最高的传唱度，而是他把最细腻的那点心事，写进了这些不张扬的歌里。",
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
