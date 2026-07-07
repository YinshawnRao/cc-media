#!/usr/bin/env python3
"""Male narration for 郭静最被低估的5首歌.

Countdown 5 -> 1 (#1 = 不药而愈, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 下一个奇迹 = 陈小霞 曲 / 姚若龙 词（与《下一个天亮》同班底的"纯爱姊妹曲"，2011《陪着我的时候想着她》）。
- 本来       = 徐佳莹 词曲自创（2011《陪着我的时候想着她》）。
- 一个人弹琴 = 刘淑莉 词曲（2007 首张专辑《我不想忘记你》）→ 文案不得说"她写的"。
- 慢慢纪念   = 林夕 词 / 易桀齐 曲（2008《下一个天亮》）。
- 不药而愈   = 王雅君 词曲（2008《下一个天亮》，与国民曲《下一个天亮》同碟易被盖）。
专辑英文名/外文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
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
    "intro": "提到郭静，很多人先想到的，是《下一个天亮》《心墙》那两首传遍大街小巷的国民情歌。可在这些大热之外，她还藏着不少安静、干净、却被严重低估的好歌。今天这期，我们从第五名倒数，盘一盘郭静最被低估的五首歌。",
    "p5_qiji": "第五名，《下一个奇迹》。它收在二零一一年的《陪着我的时候想着她》里，是陈小霞和姚若龙，继《下一个天亮》之后，再一次为郭静写下的纯爱姊妹曲。它延续了郭静最被认可的那种叙事，唱的是一个人在受过伤之后，依然愿意去相信下一个奇迹。温柔、明亮，却一点都不幼稚。只是它没能像《下一个天亮》那样传开，慢慢就成了一首被忽略的遗珠。",
    "p4_benlai": "第四名，《本来》。它同样来自《陪着我的时候想着她》，由徐佳莹一手包办词曲，气质特别细。它唱的不是控诉，也不是崩溃，而是停在'本来可以'这三个字里的那种遗憾。本来可以继续，本来可以再靠近一点，本来可以有一个不一样的结局。两个字很轻，可越听越疼。",
    "p3_tanqin": "第三名，《一个人弹琴》。它来自二零零七年郭静的首张专辑《我不想忘记你》，气质很安静，也很有画面感：一个人，一架琴，一段没说完的心事。它不是那种一听就抓耳的旋律，却特别能听见郭静早期声音里的清澈和孤单。放在遗珠榜里，它像一张被很多人错过的青春侧写。",
    "p2_jinian": "第二名，《慢慢纪念》。它收在二零零八年的《下一个天亮》里，由林夕填词，易桀齐谱曲。比起同张专辑那首同名的《下一个天亮》，它没那么抢耳，却特别耐听。它唱的不是激烈的失恋崩溃，而是回忆还在，人也在慢慢往前走。郭静很适合这种不喊不闹的表达，像把旧事轻轻收进抽屉，不常打开，却一直都在。",
    "p1_buyao": "第一名，《不药而愈》。它和《慢慢纪念》一样，收在那张《下一个天亮》里，词曲都出自王雅君。可同张专辑里有《下一个天亮》这种国民级的记忆点，《不药而愈》很容易就被盖了过去。但它其实最能代表郭静早期那种纯爱女声的疗愈感：不是轰轰烈烈地走出来，而是某一天突然发现，伤口好像没那么痛了。它轻、干净、真诚，越听，越有一种慢慢复原的力量。这，才是最被低估的郭静。",
    "outro": "五首歌盘完。第五，下一个奇迹；第四，本来；第三，一个人弹琴；第二，慢慢纪念；第一，不药而愈。郭静从来不只是那个唱大情歌的国民嗓音，她也很会用最轻、最干净的方式，把一整段心事慢慢讲给你听。这些被大热歌盖住的遗珠，刚好补全了她最安静、也最被低估的另一面。",
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
