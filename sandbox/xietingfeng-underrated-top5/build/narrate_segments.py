#!/usr/bin/env python3
"""Male narration for 谢霆锋最被低估的5首歌.

Countdown 5 -> 1 (#1 = 潜龙勿用, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 潜龙勿用 = 收录于《玉蝴蝶》(2001)，谢霆锋作曲 / 林夕填词，电影《恋爱起义》插曲。
- 苦海孤雏 = 收录于《Reborn》(2003, 第15张专辑/第8张粤语专辑)，林夕为纪念张国荣而作词。
- 不散 = 收录于《Listen Up》(2004-05)，谢霆锋作曲 / 周耀辉填词。
- 怕黑 = 收录于《One Inch Closer》(2005)，同碟主打《塞车》《狼》。
- 罗生门(国) = 收录于《无形的他全精选》(2002)，首张国语新曲+精选辑的四首新歌之一。
专辑英文名/外文一律不进配音，只进屏幕字幕。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。
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

VOICE = "zm_yunxi"
SR = 24000

# Kokoro/misaki[zh] 长句（~15s+ 独立 pipeline() 调用）有个偶发 bug：会吞掉开头第一小句
# （不管内容是什么，"第X名，" 首当其冲，因为它永远是每段的第一句）。见 2026-07 排查记录
# （CONVENTIONS.md 配音规范）。修法：给每段前面加一个无关紧要的垫话，垫话本身会被模型吃掉
# （验证：加了之后总时长几乎不变、垫话本身在音频里听不到），真正内容就不再是"第一句"而正常发声。
# outro_cta 是全系列共用的固定 CTA、且本身较短未复现该 bug，不加垫话（保持逐字照念）。
# 垫话有时会被完整吃掉（听不见），有时会漏出声（但内容不受影响）——"接下来，"漏出来配在
# "第X名" 前面读起来自然；outro 开头是总结句不是"接下来"语境，漏出来会别扭，改用更百搭的"那，"。
LEAD_GUARD = "接下来，"
LEAD_GUARD_OVERRIDE = {"outro": "那，"}

BLOCKS = {
    "intro": "提起谢霆锋，很多人先想到的，是《谢谢你的爱1999》《因为爱所以爱》《香水》这些人人会哼的经典，或者是他后来转型做美食节目、当赛车手的另一面。可翻开他这些年的专辑，还藏着一批被主打歌盖住的好作品，摇滚也好，情歌也好，都很有他自己的态度。今天这期，我们从第五名倒数，盘一盘谢霆锋最被低估的五首歌。",
    "p5_luoshengmen": "第五名，《罗生门》。它收录在二零零二年的《无形的他全精选》里，是这张国语新曲加精选辑里的四首新歌之一，可惜大众记忆大多还是被《谢谢你的爱1999》《因为爱所以爱》《香水》这些更熟悉的老歌占满，新歌反而容易被忽略。歌名本身就很有画面感：同一段关系，同一件事，每个人心里的版本却完全不一样。这首歌不是谢霆锋最热血的一面，而是更偏都市、悬疑、充满关系迷局的一面，作为倒数第五名开场，很能说明他的国语作品远不止情歌那么简单。",
    "p4_pahei": "第四名，《怕黑》。它收录在二零零五年的《One Inch Closer》里，同张专辑有主打歌《塞车》《狼》这些更有态度标签的作品，把《怕黑》整个盖了下去。这首歌的概念其实很清楚：不是简单说害怕黑夜，而是把一个人面对孤独、面对情绪暗处时那种不肯轻易示弱的脆弱唱了出来。谢霆锋的声音本来带一点冷感和锋利感，唱这种表面硬气、其实很怕的心事，反而特别有说服力。",
    "p3_busan": "第三名，《不散》。它收录在《Listen Up》专辑里，是谢霆锋自己作曲、周耀辉填词的作品，据说当年制作人觉得这首歌太好，特意把它留给了谢霆锋自己唱。它不是传统意义上的情歌，编曲带着一点迷幻摇滚的味道，更像写给一段友情、一场离别的告白：人也许早就走远了，可有些东西，始终没有真正散掉。它没有那些大热金曲的记忆点，却能听见谢霆锋作为创作人、比较少被路人注意到的那一面。",
    "p2_kuhaiguchu": "第二名，《苦海孤雏》。它收录在二零零三年的《Reborn》里，是林夕为纪念张国荣特别写下的词。同张专辑还有《第二世》《边走边爱》这些更容易被记住的歌，《苦海孤雏》反而像藏在专辑深处的情绪暗涌。它不是谢霆锋最炸裂的摇滚，也不是最讨喜的情歌，而是一种孤独、漂泊、被命运推着走的沉重感，唱法克制又冷。谢霆锋唱这种旧港乐式的伤感，很有那种少年老成的倔强。",
    "p1_qianlongwuyong": "第一名，《潜龙勿用》。它收录在二零零一年的《玉蝴蝶》里，是谢霆锋自己作曲、林夕填词的作品，这张专辑也被很多乐迷认为是香港二十一世纪以来最好的摇滚专辑之一。可同一张专辑里有《玉蝴蝶》这种更容易被记住的作品，把它的锋芒盖住了不少。它不是普通情歌，弦乐、摇滚和大气编曲揉在一起，气势十足，也很有谢霆锋那个阶段想认真做音乐的野心。歌名本身就很有分量：不是已经腾飞的龙，而是还在蓄力、还没真正出手的状态。这，才是最被低估的谢霆锋。",
    "outro": "五首歌盘完。第五，罗生门；第四，怕黑；第三，不散；第二，苦海孤雏；第一，潜龙勿用。谢霆锋从来不只是那个耳熟能详的情歌小天王，也不只是后来那个做菜、赛车的谢霆锋，他在音乐里藏着更倔、更冷、更有态度的一面。这些被大热金曲盖住的遗珠，刚好补全了最被低估的谢霆锋。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        guard = LEAD_GUARD_OVERRIDE.get(key, LEAD_GUARD)
        synth_text = text if key == "outro_cta" else guard + text
        chunks = [audio for _, _, audio in pipeline(synth_text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:22s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
