#!/usr/bin/env python3
"""女声旁白 zf_xiaoyi（温柔怀旧）。逐字稿照念，口播里 OST→中文(主题曲/影视歌曲/剧歌)，屏幕保留 OST。
全片旁白都生成（intro/各转场/各首/作品outro/固定CTA），样片只用 intro+trans1+s1_voice。
最后一段固定 CTA = FIXED_OUTRO_CTA（硬约束，见 CONVENTIONS「固定结尾配音」），永远排在作品 outro 之后。
作品 outro 不得自带投票/「哪一首最意外」问句（防双 CTA）——已从 brief 结尾删除，交给固定 CTA。
"""
import json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到张韶涵的影视剧歌曲，很多人第一反应，是《海豚湾恋人》，或者《公主小妹》。但其实，她的专辑里，还藏着不少电视剧的片头、片尾，和主题曲。有些歌你可能听了很多年，却从来没把它，和那部剧联系起来。这一期，我们不盘点最出名的那几首，只翻几首真正容易被忽略的，张韶涵隐藏剧歌。看看哪一首，会突然点亮你的，童年记忆。",

    "trans1": "第一首。很多人听过这首歌的副歌，却未必知道，它也曾经和一部韩剧，绑定过。",
    "s1_voice": "《不痛》这首歌，本身就有很强的韩剧感。它不是那种轻轻放下的歌，而是明明很痛，却一直告诉自己不能痛。放到《你来自哪颗星》的爱情故事里，这种拉扯感会更明显。张韶涵唱这首歌的时候，声音不是软弱的，而是带着一点倔。像是眼泪快掉下来了，但还是要把最后一句，唱完整。这也是她早期很多影视歌曲最迷人的地方：不是只负责好听，而是真的能把剧情的伤口，唱出来。",

    "trans2": "第二首。名字听起来很轻，但情绪，一点都不轻。",
    "s2_voice": "《白白的》可能是这几首里面，最容易被路人忽略的一首。但它作为韩剧《贝多芬病毒》的片尾曲，气质其实很对。这首歌的情绪不是大哭大闹，而是空掉以后，整个人，还站在原地。张韶涵的声音在这里，有一种很透明的破碎感，像是明明想把一切说清楚，却发现心里，已经白了一大片。所以它不是甜歌，也不是普通的伤情歌，它更像一首，很冷的片尾曲。",

    "trans3": "第三首。是很多老粉心里的冷门神曲。歌名很简单，情绪却很重。",
    "s3_voice": "《真的》这首歌，在张韶涵的专辑里，一直不算最爆的那一类。但它厉害的地方，是情绪特别浓。放在《风尘三侠之红拂女》这种古装江湖故事里，反而很贴。它不是小女生的撒娇，也不是简单的失恋，而是一种明明用力爱过，却还是要接受命运分岔的，感觉。这首歌的副歌一出来，真的很像老式电视剧的片尾：故事结束了，遗憾，才刚刚开始。",

    "trans4": "第四首。很多人知道这首歌，却未必记得，它曾经出现在一部早年的偶像剧里。",
    "s4_voice": "《其实很爱你》是那种歌名一出来，就有早年偶像剧味道的歌。它没有特别用力地哭喊，但每一句，都像在假装放下。放在《屋顶上的绿宝石》里，它就是很典型的片头曲气质：一开口，人物关系、青春遗憾、错过和拉扯，全都铺开了。这首歌其实特别适合重新被听见，因为它不是靠大爆点赢的，而是靠那种，嘴上不说，心里却全是你的，后劲。",

    "trans5": "最后一首。很多人只记得它后来成了励志神曲，却忘了，它最早也有一层，电视剧的滤镜。",
    "s5_voice": "现在提到《隐形的翅膀》，很多人想到的是高考、励志、合唱、晚会。但放回当年的语境里，它其实也和《爱杀十七》，有很深的连接。这部剧的气质并不明亮，甚至有点冷、有点疼。所以这首歌在这里听起来，就不只是我要飞，更像是一个受过伤的人，还想把自己，一点点撑起来。这也是为什么，它后来能走出电视剧，变成很多人心里的，安慰。",

    # 作品自身 outro：内容总结 + 升华，收在歌手特质上。**不带投票/问句**（交给固定 CTA）。
    "outro": "所以张韶涵的影视剧歌曲，真的不只有《海豚湾恋人》和《公主小妹》。有些歌后来成了金曲，有些歌留在了老剧的片尾，还有些歌藏在专辑里，等很多年以后，才被重新想起。如果不是重新翻这些老歌，可能真的会忘了，原来她的声音，曾经陪过，这么多电视剧的结尾。",

    # 固定引流 CTA：全片最后一句，逐字固定，禁改（outro_cta.py / CONVENTIONS「固定结尾配音」）。
    "outro_cta": FIXED_OUTRO_CTA,
}

ONLY = set(sys.argv[1:])  # 传 key 只生成子集，如 `narrate.py intro trans1 s1_voice`
A = Path("audio"); A.mkdir(exist_ok=True)
pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    if ONLY and key not in ONLY:
        continue
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:11s} {meta[key]['dur']:6.2f}s")

# 合并已存在的 narration.json（增量生成时不丢已生成段）
nj = Path("narration.json")
allmeta = json.loads(nj.read_text(encoding="utf-8")) if nj.exists() else {}
allmeta.update(meta)
nj.write_text(json.dumps(allmeta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL(this run)", round(sum(m["dur"] for m in meta.values()), 2), "s")
