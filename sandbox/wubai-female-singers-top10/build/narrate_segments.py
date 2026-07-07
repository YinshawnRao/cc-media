#!/usr/bin/env python3
"""男声旁白：伍佰给女歌手写的歌 TOP10。

倒数揭晓 10 -> 1。英文（China Blue 等）不进配音（Kokoro 念不好），只作屏幕文字。
结尾固定 CTA 从 tools/video/outro_cta.py 导入（仓库级硬约束）。
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

VOICE = "zm_yunxi"   # 默认男声
SR = 24000

BLOCKS = {
    "intro": "提到伍佰，你脑子里大概是浪人情歌，是那个甩着长发、满嗓子嘶吼的摇滚浪子。可你也许没注意，他还有另外一支笔，专门写给女歌手。王菲、那英、苏慧伦、王心凌，都唱过他写的歌。今天这十首，全是伍佰写给女声的作品，我们从第十名，一路倒数到第一名。",
    "p10": "第十名，黄小琥的《突然的自我》。这首歌，大家更熟的是伍佰自己唱的版本，但它本来就是伍佰一手包办的词曲。换成黄小琥那把又厚又沧桑的嗓子，那句潇洒走一回的洒脱里，反而多了一层过来人的疲惫和认命。",
    "p9": "第九名，郁可唯的《你不要我了吗》。原来郁可唯，也唱过伍佰。这是伍佰难得写得这么柔软的一首，他把一个人被丢下的时候，那句最不敢问出口的话，直接写成了歌名——你，不要我了吗。",
    "p8": "第八名，杨乃文的《一个人》。严格讲，这首的曲是林暐哲写的，而词，是伍佰填的。可你听杨乃文那股又冷又硬、带着自尊的劲，配上伍佰那种直白不绕弯的句子，简直是天生一对。",
    "p7": "第七名，刘若英的《最初的地方》。奶茶的代表作太多了，这一首很容易被盖过去。但伍佰给她的旋律，带着一点率性的民谣摇滚味，让一向擅长娓娓道来的刘若英，难得唱出了几分洒脱。",
    "p6": "第六名，万芳的《夜照亮了夜》。这是一首高级的遗珠。伍佰没有给万芳写那种撕心裂肺的爆发，而是写了一盏暗处的灯——不刺眼，却能一点一点，把整个夜都照亮。",
    "p5": "第五名，那英的《我不是天使》。那英的大嗓，给人的印象向来是正面硬刚。可伍佰偏偏写得很柔，逼出了那英少见的脆弱。原来天后，也有不想再逞强的时候。",
    "p4": "第四名，王菲的《单行道》。这是个不小的冷知识——王菲，也唱过伍佰写的歌。而且不是随便跨刀，从作曲到编曲、演奏，都是伍佰和他那支乐队亲自操刀。那股慵懒又疏离的味道，和王菲的声音，意外地搭。",
    "p3": "第三名，莫文蔚的《坚强的理由》。这一首，是伍佰和莫文蔚的对唱。伍佰把坚强，写成了一种快要塌掉的状态，而莫文蔚一开口，那种都市废墟般的苍凉感，一下子就全出来了。",
    "p2": "第二名，苏慧伦的《被动》。这是女声唱伍佰，最成功的一次。苏慧伦唱得很轻很淡，可伍佰给的旋律骨架却很硬。所以这首歌最妙的地方在于：听起来温柔，骨子里，其实非常倔。",
    "p1": "第一名，王心凌的《我会好好的》。它是甜心王心凌的整个体系里，最反甜的一首。不撒娇，不哭闹，伍佰写的，是一句倔强的硬撑——我已经快不行了，但我会好好的。这，就是伍佰藏在女声里，最厉害的杀伤力。",
    "outro": "十首歌，十个不同的女声，背后却是同一个伍佰。原来那个写浪人情歌、唱台语摇滚的浪子，把自己最细腻、最克制的那一面，全都悄悄写进了别人的歌里。听完才发现，伍佰，从来不只是那个嘶吼的伍佰。",
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
        print(f"{key:10s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
