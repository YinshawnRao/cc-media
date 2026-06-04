#!/usr/bin/env python3
"""全片旁白：女声 zf_xiaoyi。开头精简(~11s)，每首 voice+mid，4句反差转场，结尾互动。
英文歌名旁白说"小太阳"，字幕保留 English。"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"; SR = 24000; SPEED = 1.03
OUT = Path("/Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet/audio")
OUT.mkdir(parents=True, exist_ok=True)

BLOCKS = {
 # ===== 开头：精简，~11s，迅速进入 =====
 "intro": "认识郭采洁，很多人是从顾里开始的——短发、红唇、冷脸。可在那之前，她其实是个古灵精怪的甜妹。这五首早期甜歌，带你看看顾里之前的她。",

 # ===== No.5 又圆了的月亮 =====
 "s5_voice": "先从第五名说起，《又圆了的月亮》。它的甜不是糖果味，是月光味——表面像在慢慢放下，可每一句里，又都藏着一点舍不得。这还不是顾里，但她已经开始，有了自己的一点点小锋利。",
 "s5_mid": "还没学会冷脸，她先学会了，自己把自己哄好。",
 "t5_4": "你看，还没到顾里的冷脸时期，她其实已经，有点小倔强了。",

 # ===== No.4 快一点 =====
 "s4_voice": "第四名，《快一点》。这是早期郭采洁最鲜明的清新感——声音很亮，节奏很轻，像一颗跳跳糖，旋律一响，全是台湾偶像剧的阳光味。那时候的她，会认真期待、会小鹿乱撞，会把喜欢，唱得特别直接。",
 "s4_mid": "喜欢一个人，连呼吸都想催它——快一点。",
 "t4_3": "而且甜妹啊，也不是只会撒娇，她还可以，很鬼马。",

 # ===== No.3 卡通人生 =====
 "s3_voice": "第三名，《卡通人生》。这一首我愿意叫它可爱暴击。它甜得很不现实，像把一整段恋爱画成了漫画分镜：有王子、有幻想、有小女生自己的小剧场。跟后来那个冷脸顾里一比，反差直接拉满。",
 "s3_mid": "她把人生过成了卡通，连烦恼，都是彩色的。",
 "t3_2": "你以为她是后来才有气场的？其实早期的甜里，就已经藏着一点锋利。",

 # ===== No.2 爱异想 =====
 "s2_voice": "第二名，《爱异想》。这是甜妹，和未来顾里之间，最妙的一段过渡。它的甜不是软的，是嘴硬型的——有点跩、有点机灵，明明很期待爱情，偏要唱得古灵精怪。顾里的锋利不是凭空冒出来的，它只是早期，被包在了一层甜里。",
 "s2_mid": "她的甜里有怪，有想法，还有一点点，酷。",
 "t2_1": "而最后这一首，才是本期真正的——小太阳。",

 # ===== No.1 Little Sunshine =====
 "s1_voice": "第一名，必须是它。如果要用一首歌，证明顾里之前的郭采洁到底有多甜，那一定是这首小太阳。它的甜不腻人，是清爽的甜，像夏天早上一把拉开窗帘，阳光直接扑到你脸上。后来她可以是气场全开的顾里，可在这首歌里，她就是一颗，亮亮的小太阳。",
 "s1_mid": "气场可以后天再长，可这份亮，是她本来就有的。",

 # ===== 结尾 =====
 "outro": "所以你看，郭采洁不是某一天突然变成顾里的。她只是从一个清亮的、古灵精怪的、甜得很有想法的女生，慢慢长出了后来那股锋利。顾里之前，她明明，就是个甜妹啊。你是从哪一首歌认识她的——甜妹时期，还是顾里时期？评论区告诉我。",
}

pipeline = KPipeline(lang_code="z")
meta = {}
for key, text in BLOCKS.items():
    chunks = [a for _, _, a in pipeline(text, voice=VOICE, speed=SPEED)]
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(OUT/f"{key}.wav", audio, SR)
    meta[key] = {"text": text, "dur": round(len(audio)/SR, 3)}
    print(f"{key:10s} {meta[key]['dur']:6.2f}s")

(OUT/"full_narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
tot = round(sum(m["dur"] for m in meta.values()), 1)
print(f"TOTAL narration {tot}s  (intro={meta['intro']['dur']}s)")
