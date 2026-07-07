#!/usr/bin/env python3
"""Male narration for 范晓萱最被低估的5首歌.

Countdown 5 -> 1 (#1 = 看不见, the climax). 倒数揭晓。
事实口径（已核实，见 SOURCES.md，避免文案出错）：
- 三张专辑全是「范晓萱」个人专辑，NOT 范晓萱&100%乐团（乐团 2007 才成立）。
- 《我要我们在一起》= 1999（金曲奖最佳专辑）；《绝世名伶》= 2001（爵士）；《还有别的办法吗》= 2004（极简钢琴日记）。
- 创作署名（关键，不能臆测）：
    看不见       —— 范晓萱 词曲（全本人）→ 可说"她一个人写的"
    都是你       —— 陈韦伶 词曲（不是她）→ 文案不得说"她写的"，只描述她的演绎
    You Don't Trust Me At All —— 范晓萱 词曲 → 可说"词曲都是她"
    失控的胖子   —— 范晓萱 作曲 / 词为范晓萱+小S 合写 → 说"她作曲、和小S一起写词"
    因为         —— 范晓萱 作曲 / 词为大S（徐熙媛）→ 说"她谱曲、大S填词"
- 英文歌名（You Don't Trust Me At All）不进配音（Kokoro 中英混读差），用"一首英文歌名的爵士作品"指代；屏幕字幕保留英文。
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
    "intro": "提到范晓萱，很多人第一反应，还是那个唱《健康歌》《我爱洗澡》的可爱小魔女。可那，只是她的起点。从一九九九年开始，她一次次推翻自己：迷幻、爵士、极简，越走越远，也越来越被低估。今天这期，我们从第五名倒数，盘一盘范晓萱最被低估的五首歌。",
    "p5_pangzi": "第五名，《失控的胖子》。它来自二零零一年的爵士专辑《绝世名伶》，由范晓萱作曲，她和小S一起填的词。光看歌名你就知道，这首有多敢玩：戏谑、古怪，还带着一点和正经爵士编制故意错位的趣味。它不是那种讨好耳朵的好听情歌，可正是这种不正经，最能体现她的创作个性——敢玩、敢怪，把一个不讨喜的题材，唱得活灵活现，满是画面。",
    "p4_yinwei": "第四名，《因为》。它收在二零零四年的《还有别的办法吗》里，那是范晓萱在情绪最低谷时，一个人写下的专辑，钢琴极简，整体灰暗，像一本几乎没有字，情绪却很深的音乐日记。《因为》由她谱曲，大S填词，不华丽，也不复杂，反而像一个人，把心里最深的话，轻轻放了出来。越安静，你越能听见她的脆弱，和诚实。",
    "p3_trust": "第三名，同样来自《绝世名伶》，是一首英文歌名的爵士作品，词和曲，都出自范晓萱本人。它不是路人最熟的那个范晓萱，可你能清楚地听见，她在爵士里那种松弛、俏皮，又带一点冷感的样子。它不靠流行旋律抓人，而是靠气质，靠节奏，靠一种态度，慢慢把你留下来。",
    "p2_dushini": "第二名，《都是你》。它来自一九九九年的《我要我们在一起》，那张拿下金曲奖最佳专辑的转型之作。比起同张的主打，《都是你》很容易被盖过去，可它的迷幻氛围和情绪包裹感，特别强。范晓萱在这张里，已经彻底甩掉早期的可爱标签，用更前卫、也更不安全的方式表达自己。这首歌不是第一耳就爆，却很耐听，像一个人被关系困住之后，嘴上轻轻说着，心里其实早就翻涌。",
    "p1_kanbujian": "第一名，《看不见》。它同样收在《我要我们在一起》里，词和曲，全部出自范晓萱一个人之手。同张专辑有更好记的主打，把它整个盖住，可它，其实最能代表转型后的范晓萱：不甜美，不是儿歌，也不是传统情歌，而是把那些看不见的情绪、关系里的不确定，还有一点点失控感，全都唱了出来。它不靠大副歌取胜，却越听越有她后来独立表达的雏形。这，才是最被低估的范晓萱。",
    "outro": "五首歌盘完。第五，失控的胖子；第四，因为；第三，绝世名伶里那首英文歌名的爵士小品；第二，都是你；第一，看不见。范晓萱从来不只是那个唱儿歌的小魔女，她更是一个敢一次次推翻自己、亲手写歌的创作者。这些被光环和标签盖住的遗珠，刚好补全了她最前卫，也最被低估的另一面。",
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
