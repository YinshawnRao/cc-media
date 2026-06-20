#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 潘玮博最被低估的5首歌 (countdown 5->1).

Hard rules (see design.md / CONVENTIONS):
- Female voice zf_xiaoyi (brief: 开头/转场/结尾都女声).
- Intro must NOT reveal the ranking. Outro reveals it (5->1).
- Outro (作品自身) must NOT carry a vote/interaction ask (防双 CTA);
  the fixed CTA (outro_cta) is the very last line, verbatim.
- 避开英文 token（Kokoro misaki[zh] 中英混读会断）：不写 Will Power / MVP / UUU 等。
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
    "intro": "提到潘玮博，很多人第一时间想到的，是《不得不爱》这些会唱会跳的舞曲，是那个全能的嘻哈偶像。可如果只听过那几首爆款，其实你漏掉了他很重要的一面。今天这五首，是潘玮博最被低估的歌——有他真正想做的中文说唱，也有藏在嘻哈专辑里的温柔情歌。先不公布完整排名，我们从第五名开始，一首一首慢慢听。",
    # 5 寂屋出租 (零零七 2008)
    "p5_jiwu": "第五名，《寂屋出租》。它收录在《零零七》这张专辑里，同张更出圈的是《双人舞》，后来大家更熟的，也是那首《亲爱的》。《寂屋出租》就像藏在专辑中段、一间没人住的空房子。它不靠大副歌砸人，而是用氛围和孤独感慢慢铺开，越听越有味道——很适合放进老歌迷的私藏歌单。",
    # 4 机会 (反转地球 2007, 南拳妈妈巨炮 + 方文山)
    "p4_jihui": "第四名，《机会》。《反转地球》这张专辑话题太多，同名主打、《着迷》《我想更懂你》都比它更常被提起。可《机会》其实很特别——这是潘玮博第一次尝试抒情摇滚，合作阵容也很有看点：南拳妈妈的巨炮，加上方文山填词。它不像潘玮博典型的快歌，也不是常规情歌，反而有一种转型试探期的特殊味道。",
    # 3 我们都怕痛 (808 2012)
    "p3_paitong": "第三名，《我们都怕痛》。提到《808》这张专辑，大家先想到的，往往是《全面通缉》《小小蚂蚁》这些更有舞曲和画面感的歌，《我们都怕痛》反而没那么大众。但它的情绪特别准：不是撕心裂肺地哭喊，而是把恋爱里那种，谁都怕受伤、所以谁都不敢先靠近的拉扯，唱得特别到位。",
    # 2 跟我走吧 (高手 2003, 林俊杰曲 + 徐世珍词)
    "p2_genwo": "第二名，《跟我走吧》。《高手》这张专辑，被同名主打和《不得不爱》这些大热门压得太狠，《跟我走吧》就很容易被忽略。可它其实非常耐听——这是林俊杰作曲、徐世珍填词，为潘玮博量身打造的一首温柔情歌，唱的是一个男人的成熟和深情。它不是爆款脸，但旋律质感很好，像藏在嘻哈专辑里的一抹温柔侧写。",
    # 1 街头诗人 (反转地球 2007, 中文 Rap)
    "p1_shiren": "第一名，《街头诗人》。把它放在第一，是因为它最能代表潘玮博真正想做的那一面——中文说唱。《反转地球》这张专辑，本来就强调用中文写说唱、做出不一样的嘻哈文化，而《街头诗人》唱的，正是一个做说唱的人，心里那些最真实的感触和心声。它的路人存在感不高，可放进潘玮博的作品线里，分量很足。",
    # 作品 outro：揭晓排名 + 升华，绝不带投票问句
    "outro": "好了，这就是这一期，潘玮博最被低估的五首歌。第五，《寂屋出租》；第四，《机会》；第三，《我们都怕痛》；第二，《跟我走吧》；第一，《街头诗人》。你会发现，最被低估的潘玮博，往往不在那些最热闹的舞曲里，而在他认真写说唱、认真唱情歌的那些瞬间——那才是偶像光环背后，更完整的他。",
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
