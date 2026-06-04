#!/usr/bin/env python3
"""男声 zm_yunxi 旁白，纪录片节奏，速度 0.95（中等偏慢）。
TTS 里把英文歌名改成 "这首歌" / "这段旋律" 避开 Kokoro 中英混读坑；屏幕字幕保留英文。
输出 voice/<key>.wav + narration.json。
"""
import json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SPEED = 0.95
SR = 24000

# 顺序对应 brief 的 0:06 起所有 TTS 段
BLOCKS = {
    # 0:06-0:14 封面动起来
    "s01_open":     "有一首歌，被窦唯、王菲、窦靖童，都唱过。",
    # 0:14-0:24 冷开场三连切
    "s02_three":    "但它最有趣的地方，不是巧合，而是同一段旋律，真的被唱出了三种人生。",
    # 0:24-0:38 标题卡
    "s03_title":    "它像一条很长的回声，从九十年代的摇滚现场，一直传到今天。",
    # 0:38-1:25 第一章 窦唯
    "s04_douwei":   "最早的版本，来自黑豹时期的窦唯。那时候的这首歌，还不是后来意义上的安全情歌。它带着九十年代摇滚的锋利，像一个年轻人把爱、冲动、不甘，全都甩进麦克风里。",
    # 1:25-1:38 转场一
    "s05_trans1":   "几年后，它出现在王菲的演唱会上。",
    # 1:38-2:32 第二章 王菲
    "s06_faye":     "一九九九年，日本武道馆。王菲站在前面唱，窦唯在后面打鼓。这个画面太特别了：原唱者退到鼓后，另一个声音把这首歌重新带到舞台中央。王菲没有把它唱成摇滚宣言，她唱得更轻，更冷，也更像一段旧时光里忽然亮起的回声。",
    # 2:32-2:45 转场二
    "s07_trans2":   "再后来，窦靖童也唱起了这首歌。",
    # 2:45-3:32 第三章 窦靖童
    "s08_jingtong": "到了窦靖童这里，这首歌忽然有了另一种味道。她没有刻意模仿窦唯的锋利，也没有复制王菲的空灵。她唱得更松，更内收，好像不是在证明自己继承了什么，而是在用自己的方式，把一段旋律轻轻接住。",
    # 3:32-4:15 核心三人同屏
    "s09_three_p":  "所以这期真正有趣的地方，不只是一家三口都唱过这首歌，而是同一首歌，经过三个人之后，气质完全变了。窦唯唱的是年轻时的热烈，王菲唱的是舞台上的回声，窦靖童唱的是长大后的松弛。",
    # 4:15-4:45 结尾升华
    "s10_outro":    "有些歌不是被翻唱。它只是被时间带着，慢慢唱完。年轻时是热烈，后来是回声，再后来，是有人终于用自己的方式，把它接住。",
    # 4:45-4:58 片尾互动
    "s11_cta":      "你最喜欢哪一个版本？评论区聊聊。",
}

out_root = Path(__file__).resolve().parent.parent
voice_dir = out_root / "voice"
voice_dir.mkdir(parents=True, exist_ok=True)

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    if not chunks:
        print(f"FAIL: {key} 未产音频", file=sys.stderr); sys.exit(1)
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    fp = voice_dir / f"{key}.wav"
    sf.write(fp, audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:14s} {meta[key]['dur']:6.2f}s")

(out_root / "narration.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
