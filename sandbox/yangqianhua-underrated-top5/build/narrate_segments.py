#!/usr/bin/env python3
"""Male narration for 杨千嬅最被低估的5首歌.

Countdown 5 -> 1 (#1 = 只要为我好, the climax). 倒数揭晓。
事实口径（已核实，避免文案出错）：
- 吵我 / 电光幻影 = 同名专辑《电光幻影》(2004-06-25)，电光幻影为主打曲，林夕词/于逸尧曲；吵我为专辑第2首。
- 小飞侠 = 《Miriam's Music Box》(2002-11-22) 收录曲，与蔡德才合唱，蔡德才首次为她作曲，于逸尧填词。
- 照相本子 = 专辑《Miriam》(2001-09-22) 收录曲，林若宁填词。
- 只要为我好 = 1998-08-01 华星三宝（杨千嬅/梁汉文/陈奕迅）合辑《大激想》收录曲（她当时是华星新人）。
只要为我好、吵我两首全网无留存官方 MV（官方频道仅存静态封面音频/卡拉OK版），
按 CONVENTIONS「DECOUPLED」处理：音频用官方干净录音，画面借用她同期官方 MV《抬起我的頭來》b-roll。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句。

⚠ 长句(~15s+)独立 pipeline() 调用会吞掉开头第一小句（CONVENTIONS「配音规范」已记录的 Kokoro 通病）。
   每段文案前拼接垫话"接下来，"再送进 pipeline()，垫话本身会被吞掉或偶尔漏出但不影响听感。
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
PAD = "接下来，"  # 防吞字垫话，见上方文档注释

BLOCKS = {
    "intro": "提到杨千嬅，很多人先想到的，是《处处吻》《少女的祈祷》这些大热金曲，是那个够飒、够真实的师奶杀手形象。可在这些代表作之外，她还有不少被埋住的好歌，安静地藏在专辑深处。今天这期，我们从第五名倒数，盘一盘杨千嬅最被低估的五首歌。",
    "p5_chaowo": "第五名，《吵我》。它收录在二零零四年的《电光幻影》专辑里，是专辑的第二首歌，气质比她那些经典苦情歌更生活化，也带着一点任性和真实。歌名听起来很日常，却很杨千嬅：不是每段关系都要唱得惊天动地，有时候只是一个人被现实、感情、情绪不断打扰，烦得很真实。它不算最厚重的作品，却很能体现她歌里那种普通人式的情绪皱褶。",
    "p4_dianguang": "第四名，《电光幻影》。它是同名专辑的主打曲，林夕作词、于逸尧作曲，可同张专辑里《处处吻》《小城大事》《炼金术》三首冠军歌太强，反而把《电光幻影》本身盖住了。它不是传统的港式情歌，而是更空灵、更有概念感的一首：歌名就像一场短暂闪过的影像，爱情、人生、情绪都像电光一样，来得快，散得也快。它补上了杨千嬅作品里，更冷、更轻、也更有禅味的一面。",
    "p3_xiaofeixia": "第三名，《小飞侠》。它收录在二零零二年的《Miriam's Music Box》里，是她与蔡德才的合唱曲，也是蔡德才第一次为她作曲。整张专辑本来就带着一种童话幻灭的概念，《小飞侠》很能代表这种气质：听起来像童话，其实唱的是长不大、追不上、爱不到的失落。它不是路人最熟的杨千嬅，却特别适合放进遗珠榜，因为它能听见她作品里，那种用童话讲成人伤心的能力。",
    "p2_zhaoxiang": "第二名，《照相本子》。它收录在二零零一年的专辑《Miriam》里，林若宁填词，画面感很强，像一个人翻开旧照片，把曾经的快乐、旧爱和回忆，一页一页重新看过。它不是大开大合的苦情歌，而是把伤口藏在照片里都还很快乐的反差里。杨千嬅唱这种歌特别有生活感：不是站在舞台中央哭，而是像坐在房间里，看着旧相簿慢慢酸起来。越轻，越有后劲。",
    "p1_zhiyao": "第一名，《只要为我好》。它收录在一九九八年的合辑《大激想》里，是她和梁汉文、陈奕迅同期出道时的作品，那时候的杨千嬅还只是华星的新人。这首歌不是她最路人化的代表作，却非常有她情歌里那种明明很痛、还要装作很懂事的味道。歌名听起来像一句体贴，其实里面全是委屈：如果你说这是为我好，那我是不是连难过都要显得合理一点。杨千嬅最厉害的地方，就是能把这种不漂亮、不体面，却很真实的关系状态，唱出来。它不是大热金曲，却最适合老粉反复听——这，才是最被低估的杨千嬅。",
    "outro": "五首歌盘完。第五，吵我；第四，电光幻影；第三，小飞侠；第二，照相本子；第一，只要为我好。杨千嬅从来不只是那个够飒、够真实的师奶杀手，她也很会把最琐碎、最不体面的心事，安静地唱给你听。这些被大热金曲盖住的遗珠，刚好补全了她最被低估的另一面。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        padded = PAD + text
        chunks = [audio for _, _, audio in pipeline(padded, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
