#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 林宥嘉最被低估的5首歌 (countdown 5->1).

Hard rules (see CONVENTIONS):
- Female voice zf_xiaoyi (brief explicitly asks for 女性配音).
- Intro must NOT reveal the ranking (cover = title + 作品描述 only). Outro reveals it.
- TTS-safe text: write 四号病房 (not 4号病房) and 感官世界 (no slash) so Kokoro pronounces
  them correctly; on-screen cards carry the exact stylized titles (《4号病房》/《感官／世界》).
- Last spoken line is the FIXED 引流 CTA, verbatim (CONVENTIONS「固定结尾配音」硬约束).
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# 固定结尾引流 CTA —— 逐字照念，全片最后一句（优先级高于 brief）
FIXED_OUTRO_CTA = "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。"

BLOCKS = {
    "intro": "林宥嘉最被记住的，是《说谎》《浪费》那几首。但真正让人单曲循环的，常常是没做成主打的遗珠。这五首，我们从第五名开始。",
    # 5 《飞》(今日营业中)
    "p5_fei": "第五名，《飞》。在《今日营业中》里，它没有《天真有邪》《坏与更坏》那么多讨论。它不抓人，却有一种往上飞的轻盈，在专辑后段慢慢发光。",
    # 4 《4号病房》(大小说家)
    "p4_sihao": "第四名，四号病房。同样来自《大小说家》，却冷门得多。有点怪、有点暗，带着戏剧感，不是常规的失恋情歌。它让你看见，林宥嘉也能唱带着情境和角色的歌。",
    # 3 《拾荒》(大小说家)
    "p3_shihuang": "第三名，《拾荒》。它被《浪费》《傻子》盖过，却最能代表《大小说家》用音乐说故事——一个人，在故事的废墟里，捡拾还值得相信的意义。放在专辑最后，像轻轻合上一本小说。",
    # 2 《慢一点》(神秘嘉宾)
    "p2_manyidian": "第二名，《慢一点》。来自《神秘嘉宾》，被《眼色》《伯乐》盖过。小宇写曲、施人诚填词，唱的是在求快的时代里，悠闲地散个步——松弛、迷幻，全是早期林宥嘉。",
    # 1 《耳朵》(感官／世界)
    "p1_erduo": "第一名，《耳朵》。在《感官世界》里，它被《说谎》《心酸》压得太明显。可它太像林宥嘉了——不催泪，而是把那种明明听见了、却听不懂的疏离，轻轻唱出来。真爱粉，一定懂。",
    "outro": "这就是这一期，林宥嘉最被低估的五首歌。从第五到第一：《飞》《四号病房》《拾荒》《慢一点》，和第一名《耳朵》。他最迷人的，从来不是用力的高音，而是那份克制、细腻、慢慢渗进来的温柔。",
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
