#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。
杨千嬅最难的5首歌 / 倒数 5→1（#1《小城大事》压轴）。用户给定排名：
1 小城大事 / 2 可惜我是水瓶座 / 3 少女的祈祷 / 4 野孩子 / 5 假如让我说下去。
用户指定：开头/转场/结尾女性配音 → 全程女声。
TTS 安全：不含英文字母；歌名全中文；难度用中文描述。
片头不剧透排名(仅封面+作品描述)，片尾完整榜单回顾。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到杨千嬅，很多人第一反应是，她唱歌赢在感情，不在技术。可只要你自己开口唱她的歌就知道，这些歌，没有一首是好对付的。今天这五首，公认是杨千嬅最难唱的歌。我们从第五名开始。",
    "p5_jiaru": "第五，《假如让我说下去》。这是一首，情绪稳定的地狱。旋律不算最炸，难的是，要在很克制的中低音区里，唱出快要崩溃的感觉。你不能真的哭到散掉，也不能唱得太平、太淡。最折磨的地方在于，情绪的压迫已经堆到了顶点，可你的声音，还得稳稳地撑住，不能抖，也不能塌。",
    "p4_yehaizi": "第四，《野孩子》。它不靠高音吓人，难，是难在层次。这首歌最狠的一点是，词就是曲，歌词的语气、粤语的声调，和旋律贴得死死的。唱得太满，会失掉野孩子那股倔；唱得太淡，又撑不起那种又委屈、又执拗的劲。要在收和放之间，找到那条特别窄的线。",
    "p3_shaonv": "第三，《少女的祈祷》。它难在，轻快的旋律里，藏着密集的控制。这不是一首大悲歌，可粤语的咬字、往前推的节奏、起起伏伏的旋律，还有那股少女感，必须同时成立。唱重了像怨妇，唱轻了像流水账，唱得太甜，又会丢掉那种近乎偏执的祈求。",
    "p2_shuiping": "第二，《可惜我是水瓶座》。这首歌，特别考验气息和情绪的控制。副歌的旋律不算炫技，可长句很多，情绪是拧着的。高音不能喊出来，弱下去又不能发虚。它不是靠飙音取胜，而是要在一路的克制里，唱出那种放不下、又拉不住的拉扯感。",
    "p1_xiaocheng": "第一，《小城大事》。这是杨千嬅最难唱出原味的一首。难的不只是音高，而是副歌要有爆发，却不能唱成苦情的大嗓门；主歌要像在讲一个故事，副歌又要突然把情绪推开。很多人能把旋律唱准，却唱不出那种，已经把一切看破，还要体体面面地，碎掉的感觉。",
    "outro": "所以你看，杨千嬅那些听起来在用情的歌背后，其实是把最难的功夫，藏进了一句句深情里。第五，《假如让我说下去》；第四，《野孩子》；第三，《少女的祈祷》；第二，《可惜我是水瓶座》；第一，《小城大事》。这五首里，你心里最难的一首，是哪一首？评论区聊聊。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:12s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
