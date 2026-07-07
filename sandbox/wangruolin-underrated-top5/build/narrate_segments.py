#!/usr/bin/env python3
"""Male narration for 王若琳最被低估的5首歌.

Countdown 5 -> 1 (#1 = 大家的孤独, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 《博尼的大冒险》= 2011 年王若琳「全创作英文概念专辑」（她升格独立制作，入围金曲奖最佳专辑制作人）。
  聊八卦 / 漠不关心 / 复仇记 / 大家的孤独 四首全部出自这一张，且词曲都是王若琳自己写 → 可说"她写的"。
  这四首是英文演唱 → 文案不写"中文情歌"，统一框成"那张大胆的英文概念专辑"。
- 《鬼才出道》= 2024 电影《鬼才之道》中文版主题曲，王若琳**作曲**、金奖编剧陈虹任**作词** →
  只能说"她作曲/写的旋律"，不能说她写词。它是唯一一首中文歌（与四首英文曲对照）。
- #2 原 brief 的《你残忍可爱的傲慢》是许光汉的歌 feat. 王若琳（且非她创作）→ 用户已改为《复仇记》。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。专辑/歌名均中文，无外文进配音。
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
    "intro": "提到王若琳，很多人先想到的，是那把唱爵士、唱慵懒情歌的嗓音，是《迷宫》《有你的快乐》那种咖啡馆式的大众记忆。可她最迷人的一面，其实藏在那些没那么流行的作品里，尤其是那张大胆的英文概念专辑《博尼的大冒险》。今天这期，我们从第五名倒数，盘一盘王若琳最被低估的五首歌。",
    "p5_guicai": "第五名，《鬼才出道》。这是二零二四年，电影《鬼才之道》的中文版主题曲，由王若琳亲自作曲，金奖编剧陈虹任填词。歌名就很像她：古怪、灵动，带一点自嘲，又有一种我偏要用自己的方式登场的姿态。它不是早年那个温柔浪漫的王若琳，而是更戏谑、更有电影感、也更会玩角色的她。作为开场，正好补上她近年创作里，最自由、最有画面感的一面。",
    "p4_liaobagua": "第四名，《聊八卦》。它出自二零一一年那张全英文的概念专辑《博尼的大冒险》，词曲都是王若琳自己写的。歌名一听就很不主流情歌，但这恰恰是它被低估的原因。它短小、轻盈，有一种音乐剧小段落的灵活感，像几个人躲在角落里交换秘密，节奏和表情，全是戏。王若琳从来不只会唱慵懒爵士，她也很会把幽默、表演感和音乐性，揉在一起。",
    "p3_moguanxin": "第三名，《漠不关心》。它同样来自《博尼的大冒险》，是一首特别适合做风格型遗珠的歌。它不走好听情歌的路线，而是带着一点角色感和舞台感。在这张专辑里，王若琳不再只是唱一个我，而像在演一部音乐奇幻剧；《漠不关心》就有那种旁观、冷淡、又带点怪味的气质。它的好，不是要感动你，而是把你带进她那个更奇幻、更不按公式走的音乐世界。",
    "p2_fuchou": "第二名，《复仇记》。它也收在《博尼的大冒险》里，歌名就很有戏，像故事突然从轻巧的童话，拐进一段黑色幽默。在这首歌里，王若琳扮起复古女伶，又会演、又会玩角色，唱腔里藏着一点狡黠、一点荒诞，还有一点音乐剧式的表演感。它补上的，正是她作品里最会讲故事、也最会造世界的那一面。",
    "p1_dajia": "第一名，《大家的孤独》。它同样出自《博尼的大冒险》，最能代表王若琳转向概念叙事之后的创作野心。歌名很轻，情绪却很准：写的不是一个人的孤独，而是大家都孤独的那种荒诞和共感。它不像传统流行歌那样去抓副歌，却越听越能听见她后期作品里，那种童话、怪趣、又带点冷幽默的底色。这，就是最被低估的王若琳。",
    "outro": "五首歌盘完。第五，鬼才出道；第四，聊八卦；第三，漠不关心；第二，复仇记；第一，大家的孤独。王若琳从来不只是那把唱爵士、唱情歌的好嗓子，她更是一个敢玩概念、会造世界的创作者。这些被大热歌盖住的遗珠，刚好补全了她最大胆、也最自由的另一面。",
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
