#!/usr/bin/env python3
"""Male narration for 梁咏琪最被低估的5首歌.

Countdown 5 -> 1 (#1 = 失散车站, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 这 5 首全是 **粤语** deep cut（用户 brief 误把它们当成国语都市情歌，已纠正）。
- 失散车站 / 地球的住客 = 《Suddenly, This Summer》(2001-06-28，粤语)。
- 荷花 / 喜剧收场 = 《G For Girl》(2001-11-27，粤语)。荷花=林夕词/Eric Kwok(郭伟亮)曲；喜剧收场=黄伟文词/谢杰曲。
- 旅程 = 《爱自己》(1996-11-11，梁咏琪首张粤语专辑)，张美贤词/Adrian Chan曲。
- 失散车站 / 地球的住客 词曲未确认 → 文案不强行署名，只讲歌本身。
- 这几首官方上传都是「静态专辑封面 + 录音」(Art Track)，无真 MV → 画面用她本人其他 MV 蒙太奇救场（解耦），
  音频用官方录音室版。文案只讲歌，不描述画面。
英文专辑名/外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。Eric Kwok 念中文「郭伟亮」。
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

BLOCKS = {
    "intro": "提到梁咏琪，很多人先想到的，是九十年代那个清清爽爽、一头短发的玉女，是《短发》《胆小鬼》里那个邻家女孩。可在那些大热歌之外，她其实还藏着不少安静、细腻的好歌，越听越有味道。今天这期，我们从第五名倒数，盘一盘梁咏琪最被低估的五首歌。",
    "p5_diqiu": "第五名，《地球的住客》。它收在二零零一年那张粤语专辑里，可整张碟的记忆点，几乎都给了《出走地平线》《他喜欢的是你》这些主打歌，这首歌就这样被盖了过去。它最特别的，是那一点点哲学感：歌名像是把一段感情，放进了更大的世界里去看——人，不过是地球上的一个住客，很多相遇和离开，其实都由不得自己。它不是第一耳就抓人的那种歌，却有一种轻轻的、漂浮着的美。",
    "p4_xiju": "第四名，《喜剧收场》。它来自二零零一年另一张粤语专辑，由黄伟文填词。歌名听起来像个轻松的结局，可它真正好听的地方，是把一段关系里的荒唐和狼狈，唱得特别克制。不是哭到失控，也不是强撑着潇洒，而是明明心里有伤，却偏要把收场，说成一出喜剧。梁咏琪唱这种带点反差的情绪，特别有味道——声音越干净，反而越显得心酸。",
    "p3_lvcheng": "第三名，《旅程》。它来自一九九六年的《爱自己》，那是梁咏琪的第一张粤语专辑。比起《爱自己》这种更有主题的歌，《旅程》更像专辑里一段被忽略的心情。它唱的不是激烈的爱情，而是一个人在路上的状态：有离开，有收拾，也有继续往前走。那时候才二十岁的她，声音还有点单薄、有点飘，可正是这种轻盈，唱出了青春里那种还没完全说清楚的迷茫。",
    "p2_hehua": "第二名，《荷花》。它和《喜剧收场》收在同一张专辑里，由林夕填词，郭伟亮谱曲。比起同张碟的《嫌弃》《继续爱》，这首《荷花》更像藏在中段的一支安静小品。它的气质很特别：干净、清冷，带着一点东方的味道，不是梁咏琪最典型的那种情歌。它不靠爆点取胜，而是靠一种淡淡的、慢慢浮起来的美——像她声音里，最透明的那一面。",
    "p1_shisan": "第一名，《失散车站》。它和《地球的住客》收在同一张专辑里，可同碟有《出走地平线》《他喜欢的是你》这些更好记的歌，把它整个埋了下去。但它其实太有梁咏琪的味道了：不是那种大开大合的伤感，而是把在某个地方走散了的遗憾，唱得很轻。车站这个画面感很强，像一段感情停在了某个夏天——人已经走远，心却还留在原地。这，才是最被低估的梁咏琪。",
    "outro": "五首歌盘完。第五，地球的住客；第四，喜剧收场；第三，旅程；第二，荷花；第一，失散车站。梁咏琪从来不只是那个清爽的玉女，她也很会用最轻、最干净的声音，把一段心事，慢慢讲给你听。这些被大热歌盖住的遗珠，刚好补全了她最安静、也最被低估的另一面。",
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
