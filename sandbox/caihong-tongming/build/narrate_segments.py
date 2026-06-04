#!/usr/bin/env python3
"""旁白配音：同名《彩虹》盘点。默认男声 zm_yunxi（盘点解说感）。
按段切：intro(蒙太奇钩子) + 5 Part(每首 voice) + outro(评论引导)。
mid/lead 屏幕文字不配音（screen-only），故不在 BLOCKS。
中文无英文，避免 Kokoro 中英混读问题。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
SPEED = 0.96

BLOCKS = {
    # 开场钩子（蒙太奇下旁白；不公布歌单）
    "intro": "华语乐坛，有很多歌都叫《彩虹》。可你发现没有，同样是这两个字，有人唱失恋，有人唱青春，有人唱陪伴，也有人，唱热血。今天这一期，我们就来听听，几首最有代表性的《彩虹》。",

    # Part 1 动力火车 — 热血励志
    "s1": "第一种《彩虹》，不是温柔的，是往前冲的。动力火车这一版，有一种八点档主题曲式的热血。不是雨停了，才看见光；而是人就算在泥里，也要把自己唱起来。",

    # Part 2 梁静茹 / 五月天 — 同一首歌两个版本
    "s2": "第二种《彩虹》很特别，它既属于梁静茹，也属于五月天。梁静茹唱出来，是很轻的伤心，像一个人躲在雨里，慢慢想通；五月天唱出来，又变成乐团式的遗憾，像是把眼泪，一把推进了副歌里。",

    # Part 3 张惠妹 — 陪伴 / 被看见
    "s3": "第三种《彩虹》，不是写给某一段爱情，而是写给那些，一直陪在身边的人。阿妹这一首最动人的地方，是它没有把孤独唱得很惨，而是唱成了一种，被理解，被接住。",

    # Part 4 羽泉 — 千禧青春
    "s4": "第四种《彩虹》，是很多人的千禧年回忆。羽泉这一版一出来，就有很强的校园感和时代感。两个男声一开口，像是把那个年代的磁带、晚会和毕业季，全都带回来了。",

    # Part 5 周杰伦 — 青春失恋
    "s5": "最后这一首，可能是很多人看到彩虹两个字的，第一反应。周杰伦这一版最厉害的地方，不是唱得多用力，而是它把青春失恋，写得很轻。好像只是随口问了一句，哪里有彩虹告诉我，可听的人，一下就回到了自己的雨季。",

    # 结尾（评论引导，不给单一答案）
    "outro": "同样叫《彩虹》，有人唱热血，有人唱失恋，有人唱陪伴，也有人唱青春。那你心里的第一首《彩虹》，到底是谁的？评论区，交给你们。",
}

Path("audio").mkdir(exist_ok=True)
pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:8s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
