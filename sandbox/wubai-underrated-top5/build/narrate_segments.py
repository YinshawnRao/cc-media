#!/usr/bin/env python3
"""Generate female narration wavs for the Wu Bai underrated top 5 video (zf_xiaoyi)."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 倒数盘点 5->1。片头不公布名次；片尾再完整列出。
# 文案据用户描述打磨成自然口播；规避英文歌名（Kokoro 中英混读会断）。
BLOCKS = {
    "intro": "提到伍佰，大家先想到的，往往是浪人情歌、挪威的森林，还有那些跨年必放的金曲。可在这些大热之外，他还藏着几首被专辑光芒盖住的歌。今天这五首，是真爱粉一提就会点头的遗珠。我们不先公布名次，从第五名开始，一首一首，听听它们到底好在哪。",
    "p5_laibuji": "第五名，《来不及》。它收在《浪人情歌》这张专辑里，可同一张的浪人情歌、牵挂、钢铁男子都太抢耳，于是它很容易被一带而过。但它的好，恰恰在于不抢。像故事讲完之后，才慢慢补上的那一句。伍佰的歌常常厉害在后劲，这首就是，第一遍未必惊艳，听到后来才发现，那种错过和无能为力，其实一直都在。",
    "p4_feiyu": "第四名，《飞在风中的小雨》。《树枝孤鸟》里能被记住的歌太多了，心爱的再会啦、断肠诗、还有树枝孤鸟，它就容易被排到很后面。可这首的气质真的很美，有一种台语歌里少见的轻盈和漂泊。不是大开大合的悲伤，而是细细的、飘着的、落不到地的惆怅。原来伍佰不只会写硬汉，也会写这么软的孤独。",
    "p3_meiren": "第三名，《没人爱的女孩》。这首冷门得很彻底，却也最能看见伍佰最早的样子。旋律和表达都还没那么大众化，那种怪怪的、拧巴的、带点边缘感的叙事，反而是他最原始的创作个性。它不像浪人情歌那样能让全场合唱，却像一张旧照片，越看越有故事。",
    "p2_zuile": "第二名，《亲爱的，你喝醉了》。被《爱情的尽头》盖住太正常了，毕竟同一张专辑里，有挪威的森林、夏夜晚风这些被反复传唱的歌。可这首特别有伍佰早期那股粗粝又温柔的劲，不是精雕细琢的情歌，更像在街边、酒后、夜风里，突然脱口而出的一句话。它没有那张金曲脸，却满是伍佰味。",
    "p1_shouyinji": "第一名，《破碎的收音机》。它不是伍佰最摇滚、最路人化的那种情歌，也没有泪桥、晚风那样的传唱度，可它的情绪特别重。歌名像一件旧物，唱出来，却是失去联系之后的空荡，像一个人在夜里反复调着频率，明知道再也收不到了，却还是舍不得把它关掉。这就是真爱粉心里，那颗最舍不得的遗珠。",
    "outro": "最后，把这份名单完整地列一次。第五，来不及；第四，飞在风中的小雨；第三，没人爱的女孩；第二，亲爱的你喝醉了；第一，破碎的收音机。伍佰最被低估的，从来不是技术，而是这些被大热盖过、却越听越久的温柔。",
    # 固定结尾 CTA（全系列统一，逐字照念，全片最后一句；见 CONVENTIONS「固定结尾配音」）
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
