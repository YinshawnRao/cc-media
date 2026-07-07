#!/usr/bin/env python3
"""Male narration for 王力宏最中国风的5首歌.

Countdown 5 -> 1 (#1 = 花田错, the climax). 倒数揭晓。
口径（已核实，避免出错）：
- 花田错：2005《盖世英雄》第2首，Chinked-out，融京剧元素。
- 在梅边：2005《盖世英雄》，王力宏作曲，取材昆曲《牡丹亭》，末段说唱 50 秒 259 字。
- 心中的日月：2007 同名专辑，王力宏词曲，赴西藏/新疆/内蒙古/云南采风。
- 竹林深处：2007《心中的日月》专辑，藏地女声吟唱＋中国鼓＋笛＋嘻哈。
- 伯牙绝弦：2010《十八般武艺》第5首，电影《恋爱通告》概念主题曲，知音典故，编曲用古筝。
英文（Chinked-out / R&B / Hip-hop / rap / MV）一律不进配音（Kokoro 中英混读差），只进屏幕字幕；
口播改用 节奏蓝调 / 嘻哈 / 说唱 等中文。
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
    "intro": "说到把中国风真正唱进华语流行的歌手，王力宏，是绕不开的那一个。两千零五年的那张《盖世英雄》，他把京剧、昆曲、还有各地的民族音乐，一股脑揉进了节奏蓝调和嘻哈里，还给这套风格起了个专属的名字。今天这一期，我们就从第五名开始倒数，盘一盘王力宏最中国风的五首歌。",
    "p5_boya": "第五名，《伯牙绝弦》。它收在二零一零年的《十八般武艺》里，是电影《恋爱通告》的概念主题曲。歌名用的是伯牙子期、高山流水那段知音的典故，编曲里特意请来古筝高手现场弹奏，一开口，就是很浓的古典气。它不像后面几首那么炫技、那么抓耳，胜在完整、雅致、情绪稳。不一定是最大声的那一首，却很有后劲，是王力宏后期中国风里，做得最圆满的一首。",
    "p4_zhulin": "第四名，《竹林深处》。它和《心中的日月》出自同一张专辑，是被严重低估的一首。如果说后面那首是大开大合，这首就是氛围派：藏地女声的吟唱、厚重的中国鼓、悠远的笛声，全压在一段很现代的嘻哈律动上，听着就像在竹林里，凭空开了一个录音棚。它很东方，底子又很潮，放到今天听，反而比很多堆料的古风歌，更耐听。",
    "p3_riyue": "第三名，《心中的日月》。这首，是王力宏中国风的精神母题。为了做这张专辑，他跑去西藏、新疆、内蒙古、云南采风，把当地的民族音乐一段段录回来，再写成歌。所以它最打动人的，是那种辽阔感：不是江南的小桥流水，而是山川、远方、还有少数民族音乐的色彩。王力宏最难得的地方就在这里，他的中国风，不只会小桥流水的婉转，还能往那更大的一片土地上走。",
    "p2_meibian": "第二名，《在梅边》。这是五首里，王力宏野心最大的一首。它取材自昆曲《牡丹亭》，做法却非常现代：把戏曲的文本和咬字，直接接到说唱和节奏蓝调上。最狠的是结尾那段说唱，五十秒里，他一口气唱了两百五十九个字，像把一段古典叙事，硬砸进了都市的语感里。它没有《花田错》那么顺耳，第一次听信息量有点大，但要论创作的实验性，它必须进前二。",
    "p1_huatian": "第一名，《花田错》。王力宏最中国风的一首，我把它放在压轴。它真正厉害的地方在于，不是简单地往节奏蓝调上，贴一张京剧的贴纸，而是旋律、咬字、转音、还有编曲的气质，全都真正咬在了一起。副歌那句，花田里犯了错，一出来，既有古典戏曲的婉转，又有流行歌的钩子，高级，但一点都不端着。它就收在那张《盖世英雄》里，是王力宏整个中国风版图，最漂亮的一块拼图。",
    "outro": "五首盘完。第五，伯牙绝弦；第四，竹林深处；第三，心中的日月；第二，在梅边；第一，花田错。从京剧到昆曲，从藏地的吟唱到草原的辽阔，王力宏没有把中国风做成一句口号，而是真的把它，唱成了华语流行里，能稳稳站住脚的一种声音。这，大概就是他最了不起的地方。",
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
