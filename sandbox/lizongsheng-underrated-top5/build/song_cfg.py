#!/usr/bin/env python3
"""李宗盛最被低估5首 — 单一配置源（clips.py 与 full_build.py 共用，防漂移）。

倒数揭晓顺序 5->1（列表即此序）。
- 五首均为李宗盛本人现场演唱（real live footage，自带现场音轨）→ 同源同窗 asrc=None，口型同步。
- 这些 1986/1993 深专辑曲全网无棚版 MV；用李宗盛真实演唱会画面（理性与感性2006 / 既然青春留不住2016 /
  有歌之年2026），抽帧逐一确认是本人特写、避开乐手solo/全景/背身。
- 单主体但 Live 会切观众/全景/乐队 -> 一律 letterbox（crop 全宽横带，去烧词/水印后保留全宽）。
- crop 去底部烧死卡拉OK歌词；nixiang(有歌之年/Colo可乐猫)顶部右上 UP水印 -> 顶裁 62px 全宽带。
"""

# 时间常量（clips.py 与 full_build.py 一致）
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
TAIL_BUF = 3.0   # clip 末尾余量（clip_len = PRE + show + TAIL_BUF）

# 暗调/安静歌的音乐增益补偿（loudnorm 后仍偏低再抬）—— 实测后填
# 一个人(p5)现场混音偏柔，loudnorm 后副歌仍约 -16.7dB（其余4首 ~-14.5）→ +2.3dB 拉齐。
MGAIN = {"p5_yigeren": 1.3}

# 封面/片尾背景底：用「远行」理性与感性2006 李宗盛对麦特写（60s 起，首帧=居中清晰唱脸作封面）。
# 选它因为：唯一无水印源 + 经典对麦正脸（无吉他/手挡脸），脸落在标题与chips之间的中段开窗。
COVER_SRC = "raw/yuanxing_live2006.mp4"
COVER_START = 60.0
COVER_LEN = 52.0
COVER_CROP = "1280:606:0:0"
COVER_DELOGO = None

INTRO_CLIP = "vert_cover"
OUTRO_CLIP = "vert_cover"

# 倒数 5 -> 1
SONGS = [
    {  # 5 一个人
        "key": "p5_yigeren", "no": "05",
        "name": "《一个人》", "plain": "一个人",
        "tag": "十七岁写下的少年迷茫",
        "note": "蓝调摇滚的冲撞感，是他创作的一个源头",
        "vsrc": "raw/yigeren_4k.mp4", "vstart": None, "crop": "1920:840:0:0", "delogo": None, "grade": "",
        "asrc": None, "chorus": 143.0, "show": 27.0, "bright": -0.30, "sat": 1.05,
    },
    {  # 4 希望
        "key": "p4_xiwang", "no": "04",
        "name": "《希望》", "plain": "希望",
        "tag": "藏在小专辑里的家庭感",
        "note": "希望不一定宏大，也可能是孩子眼里的光",
        "vsrc": "raw/xiwang_4k.mp4", "vstart": None, "crop": "1920:808:0:30", "delogo": None, "grade": "",
        "asrc": None, "chorus": 27.0, "show": 25.0, "bright": -0.30, "sat": 1.05,
    },
    {  # 3 远行
        "key": "p3_yuanxing", "no": "03",
        "name": "《远行》", "plain": "远行",
        "tag": "一封出发前写好的信",
        "note": "离开前的整理感，想把过去慢慢放好",
        "vsrc": "raw/yuanxing_live2006.mp4", "vstart": None, "crop": "1280:606:0:0", "delogo": None, "grade": "",
        "asrc": None, "chorus": 88.0, "show": 27.0, "bright": -0.30, "sat": 1.06,
    },
    {  # 2 你像个孩子
        "key": "p2_nixiang", "no": "02",
        "name": "《你像个孩子》", "plain": "你像个孩子",
        "tag": "早期那种半说半唱",
        "note": "像坐你旁边讲心事，影响了后来很多词作者",
        "vsrc": "raw/nixiang_live.mp4", "vstart": None, "crop": "1920:948:0:124", "delogo": None, "grade": "",
        "asrc": None, "chorus": 135.0, "show": 21.0, "bright": -0.30, "sat": 1.04,
    },
    {  # 1 和自己赛跑的人
        "key": "p1_saipao", "no": "01",
        "name": "《和自己赛跑的人》", "plain": "和自己赛跑的人",
        "tag": "他最狠的人生叙事",
        "note": "真正难赢的，从来不是别人，是你自己",
        "vsrc": "raw/saipao_4k.mp4", "vstart": None, "crop": "1920:838:0:0", "delogo": None, "grade": "",
        "asrc": None, "chorus": 126.0, "show": 20.0, "bright": -0.30, "sat": 1.05,
    },
]
