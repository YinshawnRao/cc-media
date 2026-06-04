#!/usr/bin/env python3
"""批量生成女声旁白（Kokoro zf_xiaoyi），模型只加载一次。输出 audio/<key>.wav 24kHz。"""
from pathlib import Path
import numpy as np, soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"; SR = 24000
OUT = Path(__file__).resolve().parents[1] / "audio"; OUT.mkdir(exist_ok=True)

SEG = {
 "intro": "每年高考季，有个人比考生还忙。张韶涵，六月准时上岗。网友直接叫她，高考妈祖娘。",
 "s1":   "第一首，适合考前最后几天。不是安慰你别怕，是直接告诉你，怕，也先冲出去。别人递鸡汤，张韶涵递战甲。",
 "trans1":"冲出去之后，下一步，是翻过去。",
 "s2":   "第二首，特别像高考新闻里的背景音乐。只要画面里有奔跑、雨天、赶考、最后一分钟，篇章一响，故事感就来了。它不是说一切顺利，它说的是，不顺，也要把这一页翻过去。",
 "trans2":"有些路，不是晴天才走。",
 "s3":   "第三首，适合考前最累的时候。它不假装世界很轻松，它默认你会累、会崩、会被雨淋。但重点是，别停。边淋雨边走，也算赢。",
 "trans3":"但真正让张韶涵和高考绑定的，还得是这一首。",
 "s4":   "最后这首，不用多解释。隐形的翅膀，不是普通高考歌，它是很多人的考试记忆。小时候听像鸡汤，长大后才懂，它唱的不是飞得多漂亮，是摔过以后，还相信自己能飞。",
 "outro":"破茧，是冲出去。篇章，是翻过去。淋雨一直走，是撑下去。隐形的翅膀，是相信自己飞得起。所以她被叫，高考妈祖娘，不是玄学。是每年六月，张韶涵的歌，都会准时，把那口气，唱回来。",
}

pipe = KPipeline(lang_code="z")
for k, t in SEG.items():
    chunks = [a for _, _, a in pipe(t, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(OUT / f"{k}.wav", audio, SR)
    print(f"{k}.wav  {len(audio)/SR:.2f}s")
print("NARRATION DONE")
