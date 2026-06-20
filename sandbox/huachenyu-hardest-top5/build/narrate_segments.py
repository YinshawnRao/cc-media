#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。

最后一段固定为 outro_cta（引流 CTA，硬约束、优先级高于 brief，见 CONVENTIONS「固定结尾配音」）
——不要删、不要改、必须排在 outro 之后。
"""
import json
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "提到华晨宇，很多人第一反应是高音。但他真正难的，不只是唱得高，而是戏剧感、爆发力和控制力，常常要在同一首歌里同时拉满。今天这五首，从第五名开始，听他到底难在哪。",
    # 倒数揭晓 5 → 1
    "p5_yanhuo": "第五名，《烟火里的尘埃》，收录在《卡西莫多的礼物》，林夕作词。它难在反方向，不是炸，而是要把安静、孤独和细腻唱稳。弱声、气息线、真假声的边缘，再到后段情绪一点点撑开。唱太满就没了漂浮感，唱太轻又撑不起后劲。",
    "p4_woguanni": "第四名，《我管你》。这首难在摇滚的爆发和现场的体能。节奏、声压、态度和稳定性都得在线，副歌一句接一句往前推，特别耗气。唱得太规矩没态度，唱得太疯又容易失控，分寸全在那条线上。",
    "p3_hanya": "第三名，《寒鸦少年》。它的难不在某一个高音，而是整首都要维持那种冷峻、锋利、持续向上的状态。副歌要有穿透力，咬字还不能糊。唱轻了没了少年气，唱重了又变成硬吼。",
    "p2_douniu": "第二名，《斗牛》，收录在《新世界》，综合难度非常高。节奏密、段落变化多、情绪推进猛，既要有攻击性，又要保持声音的控制。说白了，唱完一遍，像打完一场比赛。",
    "p1_qitian": "第一名，《齐天》，电影《悟空传》的主题曲，自带强烈的戏剧感和角色感。难点在于吟唱、说唱、强声压和高位爆发都要兼顾，前面要孤傲，后面要炸开，还不能只靠喊。普通人唱这首最大的问题是，气势想上天，气息先落地。",
    # 作品自身 outro：内容总结 + 主题升华，收在歌手特质上。**不带投票问句**（交给固定 CTA，否则双 CTA）。
    "outro": "从第五到第一，《烟火里的尘埃》《我管你》《寒鸦少年》《斗牛》到《齐天》。华晨宇的难，从来不是单纯比谁高，而是把戏剧、爆发和控制揉进同一口气里，还要稳稳落地。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（见 outro_cta.py / CONVENTIONS「固定结尾配音」）。
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        sf.write(AUDIO / f"{key}.wav", audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:12s} {meta[key]['dur']:6.2f}s")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
