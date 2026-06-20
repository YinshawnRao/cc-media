#!/usr/bin/env python3
"""Female narration wavs for 蔡健雅最被低估的5首歌 (countdown 5->1, female VO zf_xiaoyi)."""
import json, sys
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
    "intro": "提到蔡健雅，大家先想到的，多半是《Letting Go》《红色高跟鞋》这些传唱度很高的歌。但她真正高级的地方，往往藏在那些不是主打、却越听越有味道的歌里。这一期，我们不聊大热单曲，只挑五首被严重低估的遗珠。先不公布完整排名，从第五名开始，一首一首往前听，最后再一起揭晓。",
    "p5_yishu": "第五名，《遗书》。它来自那张很向内的专辑《我要给世界最悠长的湿吻》。整张唱片几乎是蔡健雅写给自己的一场对话，围绕着脆弱、不安和安全感。《遗书》这个名字听起来很重，可它唱的不是猎奇式的沉重，而是把告别、清算，和重新面对自己，写得特别深。它没有大热歌的传播度，后劲却非常强。",
    "p4_shileyuan": "第四名，《失乐园》。《陌生人》这张专辑太经典，《陌生人》《无底洞》《夜盲症》几乎把大家的记忆占满了，《失乐园》就成了被忽略的那一首。可它恰恰是整张专辑里最锋利的一面，带着摇滚的声响和社会的反思。它不是最顺耳的蔡健雅，却能让你听见她更有态度、更不肯妥协的样子。",
    "p3_youxianquan": "第三名，《优先权》。它收在《双栖动物》里，同一张专辑的《双栖动物》《假想敌》《失忆症》都更常被提起，《优先权》就显得很低调。但它的旋律和叙事都很有都市感，唱的是一段关系里那种，我到底有没有被你放在第一位的敏感和自尊。它不算大热，却是真爱粉会默默单曲循环的那一类歌。",
    "p2_shui": "第二名，《谁》。在《若你碰到他》这张专辑里，《红色高跟鞋》和《抛物线》光芒太盛，《谁》很容易被路人错过。但它其实特别耐听。它不靠副歌的爆点取胜，而是把一段关系里的试探、落差和不确定，唱得很细。蔡健雅最适合这种不把情绪喊出来，可每一句都像在追问的歌。",
    "p1_domino": "第一名，《多米诺》。它藏在《说到爱》这张专辑的后半段，旁边都是《Letting Go》《说到爱》这些更好记的歌，于是《多米诺》一直像一颗被低估的宝藏。它不是典型的蔡健雅苦情歌，而是带着一点节奏感、循环感和宿命感，越听越能听出她身为创作人的巧思。而《说到爱》这张专辑，也让她拿下了金曲奖最佳国语女歌手，整张的完成度，本身就足够硬。",
    "outro": "最后，把这一期的排名一起理一遍。第五，《遗书》；第四，《失乐园》；第三，《优先权》；第二，《谁》；第一，《多米诺》。蔡健雅被低估的，从来不是她的唱功，而是这种把锋利、克制和巧思，都悄悄藏进歌里的本事。她最好的那些歌，很多都没有大红，可时间越久，越有人听懂。",
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
        print(f"{key:16s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
