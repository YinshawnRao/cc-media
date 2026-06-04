#!/usr/bin/env python3
"""《隐形的翅膀》5版本时间线旁白。女声 zf_xiaoyi（brief 强制），中慢速留呼吸。
年份用汉字（TTS 读音更准），无英文（misaki[zh] 不擅中英混读）。
按段切：intro + 5 段(每段 voice + 短金句 mid) + outro。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"   # 女声（brief 要求）
SR = 24000
SPEED = 0.92          # 中慢速、留停顿、怀旧朋友讲故事感

BLOCKS = {
    "intro": "有些歌，刚发行的时候，只是一首剧集的片尾曲。后来，它飞上了春晚，飞进综艺舞台，也飞进很多人的人生低谷里。《隐形的翅膀》，就是这样一首歌。今天这五个版本，我们按时间一路往后听，看同一首歌，怎么陪张韶涵，也陪一代人，慢慢长大。",

    # 2006 起点·原始
    "s1_voice": "第一个版本，要回到二零零六年。那时候的《隐形的翅膀》，还带着《爱杀十七》的剧集滤镜。张韶涵的声音很清，很亮，也很年轻。像一个人站在风里，明明还没真的飞起来，却已经先相信，自己会飞。这个版本最珍贵的地方，就是原始。",
    "s1_mid": "那时候的翅膀，<br>真的还是隐形的。",

    # 2007 破圈·春晚
    "s2_voice": "一年之后，这首歌飞上了春晚。从这一刻起，它不再只是张韶涵的代表作，而变成了很多个家庭，电视机前都听过的一首歌。春晚这一版唱得很标准，很明亮，也很稳。没有太多复杂的改编，可正因为这样，它把希望唱得很直，把力量唱得很正。",
    "s2_mid": "从偶像金曲，<br>飞成一代人的国民记忆。",

    # 2013 回望·隐形→有形
    "s3_voice": "到了二零一三年，这首歌有了一个，特别适合讲故事的版本。她没有只唱《隐形的翅膀》，而是把它，和《有形的翅膀》连在了一起。这一下，叙事就变了。早年的隐形，唱的是，我相信自己可以飞；后来的有形，更像是在说，我真的经历过风，也真的，靠自己撑了过来。所以这个版本，不只是串烧，它像她对过去的自己，做的一次回应。",
    "s3_mid": "从相信自己会飞，<br>到真的长出了力量。",

    # 2020 情绪回流·唱给自己听
    "s4_voice": "二零二零年这个版本，情绪就更重了。那一年，她在一场很安静的线上演唱会里，重新唱起这首歌。到这里，《隐形的翅膀》已经不只是观众心里的励志歌，它和张韶涵本人之间，也长出了更深的连接。她再唱的时候，已经不是二零零六年，那个刚出发的少女。声音里多了经历，也多了一种，很难用技巧去解释的东西。这个版本最打动人的地方，是它让你感觉到，原来这首歌，不只是她唱给别人听的，很多时候，它也是，她唱给自己听的。",
    "s4_mid": "这首歌，<br>也接住过唱歌的人。",

    # 2023 现在·往前飞
    "s5_voice": "最后，来到二零二三年。这个版本，特别适合做结尾。因为它没有刻意煽情，也不是单纯的怀旧，它更像是一次，成熟之后的重新确认。你能听到，她的声音还是亮的，但已经不是早年那种，单薄的亮。它更稳，更松，也更有底气。如果说，二零零六年唱的是我想飞，二零零七年唱的是大家一起相信，二零一三年唱的是我真的长出了翅膀，二零二零年唱的是这首歌也接住过我，那么二零二三年这一版就是，我还在唱，而且，我还在往前飞。",
    "s5_mid": "十七年后，<br>她还在往前飞。",

    # 结尾
    "outro": "所以《隐形的翅膀》真正厉害的地方，不是它从来没有变，而是过了这么多年，它依然能被不同年纪的人，重新听懂。小时候听，是相信自己会飞；长大以后再听，是发现，自己真的，飞过了那么多风。",
}

# mid 是屏幕金句（带 <br>），TTS 不应念出来；只给屏幕用。voice/intro/outro 才配音。
SPEAK = {k: v.replace("<br>", "") for k, v in BLOCKS.items() if not k.endswith("_mid")}

pipeline = KPipeline(lang_code="z")
meta = {}
Path("audio").mkdir(exist_ok=True)
for key, text in SPEAK.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:10s} {meta[key]['dur']:6.2f}s")

# mid 文案存入 narration.json 供 build 取屏幕文字
for k, v in BLOCKS.items():
    if k.endswith("_mid"):
        meta[k] = {"text": v}
Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
spoken = sum(m["dur"] for k, m in meta.items() if "dur" in m)
print(f"TOTAL spoken {round(spoken,2)}s")
