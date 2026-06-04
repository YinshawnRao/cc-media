#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。
莫文蔚最难的5首歌 / 倒数 5→1（#1《广岛之恋》压轴）。
用户指定：开头/转场/结尾女性配音 → 全程女声。
TTS 安全：不含英文字母（Kokoro misaki 中英混读差），歌名英文/年份数字在字幕里给。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到莫文蔚，你会想到那把慵懒、醇厚的嗓音，觉得她的歌好听，又好唱。可真一开口才知道，没一首是好唱的。今天这五首，公认是莫文蔚最难唱的歌。我们从第五名开始。",
    "p5_ai": "第五，《爱》，收录在两千零二年那张专辑里。它听起来一点都不炸，却最显功底。旋律带着爵士和蓝调那种游移的味道，气息要轻，但不能飘；真假声、弱混、转音，还有每个字落在节奏上的位置，都得分毫不差。这种歌，自己随口哼很容易，真要唱到位，太难了。",
    "p4_rgmyn": "第四，《如果没有你》。别被这份深情骗了，它的原调其实并不算低。难点不是某一个惊天的高音，而是副歌一遍一遍往上推，情绪层层加码。越到后面，气息越容易散，音色越容易变薄，喉位一抬，整首就垮了。唱一遍还行，从头到尾稳稳唱好，非常累人。",
    "p3_fuyao": "第三，《扶摇》。两千一十八年同名电视剧的主题曲，是典型的影视大歌。旋律线特别开阔，副歌要用稳定的中高音一路撑住，气息和共鸣，一点都不能散。它考的不是细腻，而是气势——开阔、层层递进，最后还得有把声音推上去的力量。对莫文蔚这种音色型歌手，这种硬机能的大歌，反而最难。",
    "p2_huxi": "第二，《呼吸有害》。它比很多人以为的，难得多。这是一首粤语大歌，副歌旋律抬得很高，情绪要彻底打开，长音要稳稳撑住，尾音还得保持粤语字头字尾的清晰。最难的是，要强，但不能粗——既要胸声的厚度，又要混声的亮度。唱虚了没有冲击力，唱重了又压着嗓子，分寸全在一线之间。",
    "p1_gd": "第一，《广岛之恋》。说它是莫文蔚最难，没人会反对。这是一首男女对唱，她的部分一直待在偏高的音区，既要顶住强烈的情绪，又要死死咬住音准。副歌必须用混声撑起来，不能虚、也不能喊，还要和男声拧出那股针锋相对的张力。一路顶到最后的持续输出——这就是为什么，多少人合唱它，都唱到一半翻了车。",
    "outro": "所以你看，莫文蔚的歌从来都不好唱。她只是用那把醇厚的嗓子，把最难的技术，唱得云淡风轻。第五，《爱》；第四，《如果没有你》；第三，《扶摇》；第二，《呼吸有害》；第一，《广岛之恋》。这五首里，你心里莫文蔚最难的一首，是哪一首？评论区聊聊。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:12s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
