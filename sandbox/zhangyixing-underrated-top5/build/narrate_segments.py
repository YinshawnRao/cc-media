#!/usr/bin/env python3
"""Male narration for 张艺兴最被低估的5首歌.

Countdown 5 -> 1 (#1 = 爱到这, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 愿 = 收录于《莲》(2020) 下半张《今生篇》，词 乔林 (Qiao Lin)。
- 马 = 收录于《PRODUCER》(2021)，李毅杰/张艺兴 词，张艺兴 曲，源自《我是唱作人2》(2020-05)。
- 晚安 = 2019-11-15发行单曲，"Lay式情歌"系列第二弹（延续《我不好》），张艺兴独立作曲，Nile Lee编曲，
  林乔作词，郑伟钢琴。
  * brief 原定第三名为《微光》，核实张艺兴完整作品列表后确认不存在此曲，第一轮 auto-mode 曾暂代为《夜》，
    用户回复后正式指定改为《晚安》，已在 SOURCES.md 记录两轮替换过程。
- 炎黄子孙 = 收录于《PRODUCER》(2021)，李毅杰/张艺兴 词，张艺兴 曲编曲，源自《我是唱作人2》。
- 爱到这(Give Me a Chance) = 收录于《梦不落雨林/NAMANANA》(2018-10-19)。
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
    "intro": "提到张艺兴，很多人先想到的，是《莲》里那句戴上我的Crown，是这就是街舞里的国风战袍，是舞台上唱跳俱佳的掌控力。可在这些大制作之外，他还写过、唱过不少更安静、更私人的作品，被这些高光整个盖住了。今天这期，我们从第五名倒数，盘一盘张艺兴最被低估的五首歌。",
    "p5_yuan": "第五名，《愿》。它收在二零二零年专辑《莲》的下半张今生篇里，同张专辑有莲这首概念感极强的主打曲，愿自然容易被忽略。它没有太强的编曲野心，更像是把一句心愿，轻轻放进歌里：不是宏大的叙事，而是很朴素的守护和牵挂。这种收着唱的克制，反而最见他嗓音里最柔软的一面。",
    "p4_ma": "第四名，《马》。它收在二零二一年专辑PRODUCER里，由张艺兴作曲，他与李毅杰共同作词，最早是在我是唱作人二上呈现的原创作品，取楚汉争霸里乌骓马的意象。马头琴混进电子节拍，一句句驾、吁的拟声词，把冲锋的画面感唱得很具体。它不是最讨喜的旋律，却是张艺兴作为音乐制作人，最有态度的一次表达。",
    "p3_wanan": "第三名，《晚安》。它是二零一九年发行的一首单曲，延续前作《我不好》的路线，是张艺兴独立作曲的深情慢歌。全曲以极简钢琴和暖心弦乐铺底，像深夜里一个人终于卸下白天的防备，慢慢和过去道别。它不靠强节奏和舞台爆发取胜，而是靠旋律、气息和情绪留下来，是张艺兴在唱跳和国风大制作之外，最内收、也最真诚的一面。",
    "p2_yanhuang": "第二名，《炎黄子孙》。它同样来自PRODUCER专辑，由张艺兴作曲编曲，与李毅杰共同作词。比起后来更出圈的国风舞台，这首歌的路人认知度并不算高，但概念完整、态度鲜明：唱的是血脉、身份和文化自觉，更像一首宣言。张艺兴一直强调的民族性和现代流行制作的融合，在这首歌里能听得非常清楚。",
    "p1_aidaozhe": "第一名，《爱到这》。它收在二零一八年专辑梦不落雨林里，同张专辑有梦不落雨林这样记忆点更强的主打曲，爱到这反而被盖住了。但它其实最能体现张艺兴在R&B和流行旋律里的细腻：不是炸场，也不是强节奏炫技，而是把一段关系走到某个节点时的停顿、拉扯和不舍，唱得很有氛围。这不是最路人向的张艺兴，却是最耐听的张艺兴。",
    "outro": "五首歌盘完。第五，愿；第四，马；第三，晚安；第二，炎黄子孙；第一，爱到这。张艺兴从来不只是舞台上那个精准到毫秒的唱跳偶像，他也很会用最安静的方式，把心事和态度，一句句唱给你听。这些被大制作盖住的遗珠，刚好补全了他最容易被忽略、却也最值得被听见的另一面。",
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
