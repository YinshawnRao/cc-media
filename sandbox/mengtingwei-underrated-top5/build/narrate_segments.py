#!/usr/bin/env python3
"""Male narration for 孟庭苇最被低估的5首歌.

Countdown 5 -> 1 (#1 = 情愿一个人, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 5 首歌 孟庭苇 本人均 **未参与词曲创作**（她只演唱）→ 文案不得说"她写的"。
  · 爱你太真      = 刘思铭 词 / 刘志宏 曲（《真的还是假的》1995）
  · 不下雨就出太阳吧 = 许常德 词 / 游鸿明 曲（《风中有朵雨做的云》1993）
  · 手语          = 林秋离 词 / 熊美玲 曲（《心言手语》1996）
  · 第二道彩虹     = 薛志雄 词 / 陈秋霞 曲（《第二道彩虹》1997，改编自陈秋霞1978原作）
  · 情愿一个人     = 楼南蔚 词 / 玉置浩二 曲（《真的还是假的》1995，玉置浩二日文 LOVE SONG 中文填词版）
专辑英文名/外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。
作品自身 outro 不得再带投票问句（防双 CTA）。
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
    "intro": "提到孟庭苇，很多人会先想起《冬季到台北来看雨》，那个被叫做月亮公主的清亮嗓音。可在这些传遍大街小巷的大热歌之外，她还有不少被忽略的好歌，安静、温柔，越听越有味道。这期，我们从第五名倒数，盘一盘孟庭苇最被低估的五首歌。",
    "p5_aini": "第五名，《爱你太真》。它收在一九九五年的专辑《真的还是假的》里，由刘思铭、刘志宏创作，藏在专辑中段，很容易被听过去。它的情绪很直接：因为爱得太真，受的伤也就格外真。没有复杂的包装，孟庭苇就那样清清淡淡地承认，原来一颗太认真的心，也会让人变得脆弱。越简单，越听得见她声音里的那份纯粹。",
    "p4_buxiayu": "第四名，《不下雨就出太阳吧》。它来自一九九三年的《风中有朵雨做的云》，许常德填词，游鸿明谱曲。光是这个歌名，就很孟庭苇：有雨，有天晴，还有一点朴素的盼望。它不是大苦情，也不是一听就抓人的旋律，更像一句轻轻的自我安慰。难过可以有，阴天可以有，但总要等到太阳出来。它好就好在不用力，把生活里的小低潮，慢慢唱开。",
    "p3_shouyu": "第三名，《手语》。它来自一九九六年的《心言手语》，林秋离作词，熊美玲作曲。这首歌的概念很特别：有些话其实说不出口，只能靠眼神、动作和沉默，慢慢传过去。比起那些月亮、雨、云的代表作，它没有那么大的记忆点，却特别适合孟庭苇来唱。不需要浓烈的情绪，她也能把那些藏得很深、很轻的心事，一点一点送到你心里。",
    "p2_caihong": "第二名，《第二道彩虹》。它是一九九七年同名专辑的主打，薛志雄作词，陈秋霞作曲，其实改编自一首七十年代的老歌，孟庭苇用更轻盈的方式，把它重新唱了一遍。歌里的意思很美：雨后真正留住你的，往往不是第一道彩虹，而是经历过以后，才慢慢看见的那一道。它不靠强烈的副歌，而是靠明亮和一点疗愈感，补上了孟庭苇作品里更有光的一面。",
    "p1_qingyuan": "第一名，《情愿一个人》。它同样收在一九九五年的《真的还是假的》里，旋律来自玉置浩二，楼南蔚重新填上了中文词。这首歌最特别的，是它写孤单的方式：不是大哭大闹，也不是怨谁，而是一个人慢慢接受，宁愿就这样独处。孟庭苇的嗓子唱这种安静，太有优势了，清淡、温柔，却越听越酸。这，才是最被低估的孟庭苇。",
    "outro": "五首歌盘完。第五，爱你太真；第四，不下雨就出太阳吧；第三，手语；第二，第二道彩虹；第一，情愿一个人。孟庭苇从来不只是那个唱月亮、唱雨的清亮嗓音，她也很会用最轻、最淡的方式，把一段段说不出口的心事，慢慢唱给你听。这些被大热歌盖过的遗珠，刚好补全了她最安静、也最被低估的另一面。",
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
