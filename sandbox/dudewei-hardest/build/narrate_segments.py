#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，输出 audio/<key>.wav + narration.json。
杜德伟最难的5首歌 / 按用户给定排名倒数 05→01。
片头不暴露榜单，片尾完整回顾排名。
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到杜德伟，很多人先想到的是会跳、会唱、很有型。但真正难的地方，是他把情歌、节奏和R&B唱法，揉成了一种很难模仿的松弛感。今天这五首，不只考音高，更考气息、律动、音色和情绪的分寸。先不剧透完整榜单，我们从第五名开始。",
    "p5_zhongai": "第五，《钟爱一生》。这首难在传统情歌的大线条。旋律宽，句子长，情绪要一路铺开，高位要有支撑，不能虚，也不能硬。它不像《无心伤害》那样强调R&B语感，也不像《把你宠坏》那样考节奏，但非常考验声音厚度、气息耐力和情绪完整度。",
    "p4_chonghuai": "第四，《把你宠坏》。快歌里的隐藏难歌，就是它。节奏推进快，歌词密度高，律动要准，气息要弹，还得保持杜德伟那种轻松又有张力的R&B唱法。唱得太用力会笨，唱得太轻又没劲。最难的是，听起来很潇洒，身体其实一直在高速运转。",
    "p3_qingren": "第三，《情人》。这首看似好唱，其实非常吃音色和气息。副歌要深情、饱满、稳定，但不能唱得油；主歌要有R&B的律动感，咬字还不能拖。它最难的地方，是高级感。声音要够贴、够暖、够稳，还要一直保留呼吸感。",
    "p2_wuxin": "第二，《无心伤害》。这首难在R&B语感和情绪拉扯。旋律不是直来直去的抒情歌，很多地方都要细腻的滑音、转音、真假声边缘和节奏弹性。普通人唱，很容易只唱出苦情，却唱不出杜德伟那种松弛、性感、内疚和克制混在一起的味道。",
    "p1_nozou": "第一，《不走》。这首是杜德伟情歌里最难稳住的一首。副歌旋律持续往高位推，长句多，气息不能断，声音还要保持厚度和深情感。最难的是不能只靠喊。越到后面，越要撑住情绪、音准和尾音。唱轻了没痛感，唱重了又容易粗。",
    "outro": "最后回顾一下这份榜单。第五，《钟爱一生》；第四，《把你宠坏》；第三，《情人》；第二，《无心伤害》；第一，《不走》。杜德伟最难的地方，不只是唱得高，而是把力量、气息、律动和性感，都藏在一种看似轻松的表达里。这五首里，你觉得最难复刻的是哪一首？",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    out = Path("audio") / f"{key}.wav"
    sf.write(out, audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:14s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
