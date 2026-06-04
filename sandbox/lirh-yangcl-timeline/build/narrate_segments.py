#!/usr/bin/env python3
"""默认男声 zm_yunxi（纪录片感）。按段切：intro + 5 首（每首 voice + 短文案）+ outro。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zm_yunxi"
SR = 24000
SPEED = 0.95  # 稍慢，纪录片感

BLOCKS = {
    # 开场钩子
    "intro": "有些歌，听第一次是旋律。听到后来，才发现它们像时间留下的暗线。李荣浩写给杨丞琳的这些作品，最动人的地方，不是甜，而是它们刚好记录了一个人，从被爱看见，到终于看见自己。",

    # 01 幸福菓子
    "s1_voice": "第一颗种子，其实来得很早。2007年，《幸福菓子》收在杨丞琳的《任意门》里。那时候的李荣浩，还不是后来站在台前的李荣浩；杨丞琳也还带着早期偶像剧时代的甜感。这首歌最有意思的地方是：它不像命中注定的宣言，更像一颗被提前放进时间里的小糖。",
    "s1_mid": "那时候，故事还没有开始。歌已经先到了一步。",

    # 02 观众
    "s2_voice": "到了《观众》，甜味退后了。李荣浩写的不再是轻盈的爱情想象，而是一个人在关系里慢慢长出的清醒。它像杨丞琳成年后的情感自白：原来爱情里，有时幸福才是主角，而我们，只是坐在台下，看它来过，也看它离开。",
    "s2_mid": "有些爱，不是输了。只是终于看清了自己的座位。",

    # 03 慢慢喜欢你
    "s3_voice": "《慢慢喜欢你》不是杨丞琳的原唱，但它必须放在这条时间线里。因为这首歌写的不是轰轰烈烈，而是日常、陪伴、变老，是一种慢到不需要证明的喜欢。后来杨丞琳唱起它，观众听到的就不只是翻唱，而像是她把一首写给时间的歌，又轻轻唱回了自己的生活。",
    "s3_mid": "慢，不是迟钝。是终于愿意把时间交给一个人。",

    # 04 献丑
    "s4_voice": "如果《慢慢喜欢你》写的是陪伴，那《献丑》写的就是亲密关系里更难的一面：我能不能把不漂亮、不体面、不好解释的自己，也交给你看？这首歌里，李荣浩参与修饰词句，它不像一句情话，更像成年人关系里的底层问题：爱一个人，到底是爱光亮，还是也能接住阴影？",
    "s4_mid": "真正亲近的人，会看见你的光，也接住你的狼狈。",

    # 05 像是一颗星星
    "s5_voice": "最后放《像是一颗星星》，不是因为它最甜，而是因为它把这条线收得最完整。李荣浩写的不是‘你属于谁’，而是‘你已经成为你自己’。从早年的甜歌，到后来的自白、陪伴、坦白，再到这首写给出道二十年的作品，真正动人的地方是：她不只是被爱着的人，她也是自己发光的人。",
    "s5_mid": "最好的情歌，不是把她写成谁的爱人。而是看见她本来就是星星。",

    # 结尾
    "outro": "所以这五首歌放在一起，像一条很温柔的线：从一颗小小的幸福果子，到一个人终于成为自己的星星。李荣浩写下的是歌，杨丞琳唱出来的，是时间。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(f"audio/{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
    print(f"{key:14s} {meta[key]['dur']:6.2f}s")

Path("narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL narration", round(sum(m["dur"] for m in meta.values()), 2), "s")
