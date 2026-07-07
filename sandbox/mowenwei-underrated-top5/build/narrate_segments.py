#!/usr/bin/env python3
"""Male narration for 莫文蔚最被低估的5首歌.

Countdown 5 -> 1（#1 = 月蚀，压轴）。
每段长旁白（intro/p1-p5/outro，~17-20s 独立 pipeline() 调用）前拼一句垫话"接下来，"，
规避 Kokoro 长句开头吞字的已知问题（见 CONVENTIONS.md TTS 规范），产出后不裁剪垫话本身
（垫话被吞或偶尔漏出都不影响听感）。outro_cta 较短（<10s）不受影响，不加垫话。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句，禁改。
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
PAD = "接下来，"

BLOCKS = {
    "intro": "提到莫文蔚，很多人先想到的，是《阴天》《盛夏的果实》《忽然之间》这些人尽皆知的大热金曲，是那把慵懒又带点戏谑的都会嗓音。可翻开她的专辑，你会发现她还藏着不少被掩埋的好歌，一样有质感，却很少被人提起。今天这期，我们从第五名倒数，盘一盘莫文蔚最被低估的五首歌。",
    "p5_aiwodeqingjushou": "第五名，《爱我的请举手》。它收在《就是莫文蔚》里，气质比她那些经典慢歌轻盈很多，也更有舞台感。它不是最典型的莫文蔚苦情歌，却很能体现她音乐里会玩的一面：有节奏感，有一点幽默，也有那种不把爱情看得太沉重的聪明。作为遗珠开场，它先让你看到，莫文蔚不只有伤感，也有松弛和明亮。",
    "p4_beijiguang": "第四名，《北极光》。它有正式的官方MV，可大众的记忆，几乎都被《盛夏的果实》《阴天》《忽然之间》这些大热歌占满了。北极光的气质很特别，带一点冷艳、遥远，和一种不一定会抵达的美感。它不是普通的都市情歌，更像一个人站在极冷的地方，静静地等一束不一定会出现的光。莫文蔚唱这类歌不需要太满，越克制，越显得孤独，也越显得华丽。",
    "p3_qishiwo": "第三名，《其实我一直都想对你说》。它不是莫文蔚最大众的代表作，却很耐听。光是歌名，就已经把情绪说得很清楚：有些话一直想说，可惜错过了时间，错过了对象，也错过了最适合开口的那个自己。它没有靠强烈的副歌制造爆点，而是把遗憾，放在更安静的位置。莫文蔚的声音，唱这种没说出口的关系，特别有故事感。",
    "p2_landeguan": "第二名，《懒得管》。它同样来自《十二楼的莫文蔚》，不是莫文蔚最常被点名的情歌，却很能听见她身上那种洒脱、独立，带一点女性自觉的锋利感。它不是温柔苦情的路线，而是把我不想再被你定义，唱得很直接。莫文蔚唱这种歌很有优势，声音里带着一种慵懒却不软弱的态度，越听越像都市女性，把主动权拿回来的那个瞬间。",
    "p1_yuedie": "第一名，《月蚀》。它同样收在《十二楼的莫文蔚》里，同张专辑有《十二楼》《寂寞的恋人啊》这些更容易被记住的作品，月蚀，就这样被悄悄盖住了。可它其实最能代表莫文蔚最迷人的都市冷感：不是大哭大闹，而是把孤单、失衡和情绪里的阴影，唱得很轻。歌名本身就有画面，像一段关系里，光慢慢被遮住，只剩下一点冷冷的余温。这，才是最被低估的莫文蔚。",
    # 作品自身 outro：内容总结 + 主题升华，收在歌手特质上。不自带投票问句（交给下面固定 CTA，否则双 CTA）。
    "outro": "五首歌盘完。第五，爱我的请举手；第四，北极光；第三，其实我一直都想对你说；第二，懒得管；第一，月蚀。莫文蔚从来不只是那个唱大热金曲的都会女声，她也很会用最轻、最克制的方式，把心事唱给你听。这些被大热歌盖住的遗珠，刚好补全了她最迷人、也最被低估的另一面。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改。
    "outro_cta": FIXED_OUTRO_CTA,
}

PADDED = {"intro", "p5_aiwodeqingjushou", "p4_beijiguang", "p3_qishiwo", "p2_landeguan", "p1_yuedie", "outro"}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        gen_text = (PAD + text) if key in PADDED else text
        chunks = [audio for _, _, audio in pipeline(gen_text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:24s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
