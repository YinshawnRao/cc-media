#!/usr/bin/env python3
"""女声旁白 (zf_xiaoyi)，逐字稿原样。输出 audio/<key>.wav + narration.json。
吴青峰最难的5首歌 / 倒数 5→1（#1《频率》压轴）。
用户指定：开头/转场/结尾女性配音 → 全程女声。
注意：Kokoro misaki[zh] 不擅长中英混读 → 旁白里不放音名(C#3/A5)等英文，改用"两个八度/头声极限"等中文表述；音名留给屏幕字幕。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000

BLOCKS = {
    "intro": "提到吴青峰，你脑子里浮现的，可能是清亮、空灵、像羽毛一样飘的高音。可正是这种听起来毫不费力的轻，藏着华语乐坛最难复刻的一种声音。它不是用力吼上去的高，而是卡在换声区里，又轻、又亮、又不能发虚。今天这五首，是公认吴青峰最难唱的歌。难，不在飙到多高，而在那条又窄又险的高位频道，普通人连进，都进不去。我们从第五名开始。",
    "p5_wohaoxiang": "第五，《我好想你》。它不一定是音最高的，却是最容易被唱毁的一首。整段副歌都要挂在高位上，情绪拉满，可声音偏偏不能变粗、不能变硬。多少人翻唱，一到副歌就开始喊、开始挤，一秒就露了馅。它考验的，是怎么把高音唱得又稳、又干净，还满是想念。",
    "p4_qifengle": "第四，《起风了》。别被它的传唱度骗了。这首歌的难，全藏在长线条的气息里。高位上的咬字要清楚，音色要清澈，却又不能唱得太薄。副歌一旦硬喊就垮，可越想唱出青峰那种通透，气息、位置和音准上的破绽，就越藏不住。听着人人会唱，真唱才知道有多难。",
    "p3_dixin": "第三，《地心》。这是吴青峰在歌手的舞台上，把轻声也能有压迫感，诠释到极致的一首。它不是一路往上飙的爽歌，而是低位慢慢地铺，再到高位猛地炸开，真假声来回切换，情绪一层一层往上递。最麻烦的是，越安静的地方，越藏不住瑕疵。看着不炸场，其实全是控制力。",
    "p2_tongkuai": "第二，《痛快的哀艳》。这是一首真正的大体量难歌。音域从最低到最高，横跨了两个八度，低音区要稳得住，高音区要冲得上去，情绪还得像交响摇滚一样，一层一层往上推。它考验的不只是嗓子，更是持续输出的体力和掌控。唱好了是一首史诗，唱塌了，就成了一场体能测试。",
    "p1_pinlv": "第一，《频率》。说吴青峰最难，把这首放在第一，没人会有异议。它几乎全程都卡在最折磨人的换声区上，又要轻、要亮、要飘，还一点都不能发虚，最高的地方，甚至顶到了头声的极限。对大多数男声来说，它的难，不是唱不上去，而是连进入这条赛道的资格，都很难拿到。这已经不是在飙高音，这是在悬崖边上，走钢丝。",
    "outro": "所以吴青峰的轻，从来都不是真的轻松。那些听起来像羽毛、像呼吸一样的高音，背后是华语乐坛最难复刻的控制力。这五首，你心里吴青峰最难的一首，是哪一首？评论区告诉我。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=1.0)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:14s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
