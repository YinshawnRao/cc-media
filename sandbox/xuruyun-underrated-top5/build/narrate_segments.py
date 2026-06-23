#!/usr/bin/env python3
"""Male narration for 许茹芸最被低估的5首歌.

Countdown 5 -> 1 (#1 = 学琴的孩子, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 透气 = 戴佩妮 词曲（许茹芸演唱）。
- 忘 = 许茹芸 本人词曲自创。
- 白纸黑字 = 许茹芸 作曲（日本制作人龟田诚治从上百首 demo 中选此曲），本人参与创作。
- 学琴的孩子 = 彭季康 词 / 李正帆 曲，许茹芸只演唱、未参与创作 → 文案不得说"她写的"。
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
    "intro": "提到许茹芸，很多人先想到的，是那个唱《如果云知道》《独角戏》的轻柔嗓音，是华语情歌里很标志的芸式唱腔。可在那些大热情歌之外，她还有不少被埋住的好歌，安静、克制，越听越有味道。今天这期，我们从第五名倒数，盘一盘许茹芸最被低估的五首歌。",
    "p5_banshou": "第五名，《半首歌》。它收在一九九六年的《如果云知道》里，可同张专辑的记忆点，几乎被《如果云知道》《独角戏》《突然想爱你》占满了，这首歌自然很容易被忽略。它有一层很淡的民谣底色，唱的是一种没说尽、也没唱完的遗憾。不是彻底告别，也不是真的放下，而像一段感情只唱到一半，就停在了那里。许茹芸那把轻盈的嗓子，唱这种留白，特别合适。",
    "p4_baizhi": "第四名，《白纸黑字》。它来自二零零一年的《只说给你听》，是许茹芸参与作曲的作品，当年还是日本制作人龟田诚治，从上百首小样里一眼挑中的。歌名就很有画面：关系里的话，一旦写成白纸黑字，就不再只是情绪，而像一种再也收不回的确认。它不是她最顺口的旋律，却特别能听出她中后期的成熟和清醒。没有夸张的起伏，可一字一句，都有一种慢慢冷下来的痛。",
    "p3_wang": "第三名，《忘》。它收在一九九九年的《真爱无敌》里，比起同张专辑的《真爱无敌》《一直是晴天》，它更像一段藏在专辑深处的私语。这首歌是许茹芸自己写的词曲，编曲也更简单，像一个人终于不再大声解释，只是轻轻地承认：有些事，真的该忘了。它最动人的地方不在用力，而在克制，越轻，反而越有后劲。",
    "p2_touqi": "第二名，《透气》。它同样来自一九九八年的《你是最爱》，由戴佩妮包办词曲，气质很特别。它不像许茹芸最典型的那种大情歌，而是更轻、更短、更有呼吸感。歌名就很准：不是哭到不能自已，而是在一段关系里，终于想要一点点空间。它没有那种炸开的爆发点，却特别耐听，像一扇突然被推开的小窗，轻轻把闷住的情绪，放了出去。",
    "p1_xueqin": "第一名，《学琴的孩子》。它同样收在一九九八年的《你是最爱》里，可同张专辑有《美梦成真》《你是最爱》这些更好记的歌，把它整个埋了下去。但它其实很特别，有一种许茹芸作品里少见的叙事感：不是传统的苦情歌，更像一个关于成长、孤独和敏感心事的小故事。旋律很安静，画面很细，越听越能感觉到，她声音里那种轻轻把故事讲给你听的能力。这，才是最被低估的许茹芸。",
    "outro": "五首歌盘完。第五，半首歌；第四，白纸黑字；第三，忘；第二，透气；第一，学琴的孩子。许茹芸从来不只是那个唱大情歌的天后嗓音，她也很会用最轻、最克制的方式，把一整段心事讲给你听。这些被大热歌盖住的遗珠，刚好补全了她最安静、也最被低估的另一面。",
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
