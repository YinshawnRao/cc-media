#!/usr/bin/env python3
"""光良最被低估5首 — 单一配置源（clips.py 与 full_build.py 共用，防漂移）。

倒数揭晓顺序 5->1（列表即此序）。
- 同源曲（如果你还爱我 / 握你的手）：footage 窗 == 音乐窗（同源同窗 -> 口型同步），asrc=None。
- 解耦曲（期限 / 海边 / 住在遥远的星球）：深专辑曲全网无 MV/Live，用录音室音频(asrc)
  + 2016 巡演慢歌 Live 做 B-roll 视频(vsrc)，两者独立；achorus 是录音室副歌入点，
  vstart 是 B-roll 视频窗起点（任意干净段，不需对口型）。
单主体居中但 Live 会切观众/全景 -> 一律 letterbox（crop 全宽横带，去污染带后保留全宽）。
delogo 去 XXmusic(楚瀏音樂)右上角标；crop 去底部 credit/烧词。
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
MGAIN = {}

# 封面/片尾背景底（计算之外单独切，见 clips.py 末尾）
COVER_SRC = "raw/ruguo_full.webm"
COVER_START = 198.0     # 钢琴特写干净段(无致敬卡片/熊猫水印),首帧作封面
COVER_LEN = 52.0
COVER_CROP = "1390:880:0:0"
COVER_DELOGO = None

INTRO_CLIP = "vert_cover"
OUTRO_CLIP = "vert_cover"

# 2016 巡演各 Live：XXmusic 角标在右上(x>=1540)、词曲 credit+烧词在底部(y>=840)。
# 用偏窄全宽横带 crop=1540:828:0:0 一次裁净（排除右上 logo + 底部 credit），无需 delogo。
TOUR_CROP = "1500:828:0:0"

# 倒数 5 -> 1
SONGS = [
    {  # 5
        "key": "p5_xingqiu", "no": "05",
        "name": "《住在遥远的星球》", "plain": "住在遥远的星球",
        "tag": "专辑后段的私藏曲",
        "note": "越安静越有后劲，像隔着很远的距离",
        "vsrc": "raw/broll_naxie.webm", "vstart": 8.0, "crop": TOUR_CROP, "delogo": None, "grade": "colorbalance=rm=0.06:gm=-0.04:bm=0.10",
        "asrc": "audio_src/xingqiu.wav", "chorus": 187.0, "show": 32.0, "bright": -0.34, "sat": 1.02,
    },
    {  # 4
        "key": "p4_haibian", "no": "04",
        "name": "《海边》", "plain": "海边",
        "tag": "《童话》里的隐藏留白",
        "note": "陈熙词曲；不煽情，把情绪放进风和海里",
        "vsrc": "raw/broll_naxie.webm", "vstart": 15.0, "crop": TOUR_CROP, "delogo": None, "grade": "colorbalance=rm=-0.07:gm=0.04:bm=0.05",
        "asrc": "audio_src/haibian.wav", "chorus": 164.0, "show": 32.0, "bright": -0.32, "sat": 1.05,
    },
    {  # 3
        "key": "p3_qixian", "no": "03",
        "name": "《期限》", "plain": "期限",
        "tag": "专辑深处的时间感遗珠",
        "note": "不是第一耳爆款，等待感越听越浓",
        "vsrc": "raw/broll_naxie.webm", "vstart": 5.0, "crop": TOUR_CROP, "delogo": None, "grade": "",
        "asrc": "audio_src/qixian.wav", "chorus": 217.0, "show": 32.0, "bright": -0.30, "sat": 1.08,
    },
    {  # 2
        "key": "p2_woni", "no": "02",
        "name": "《握你的手》", "plain": "握你的手",
        "tag": "真爱粉的遗珠",
        "note": "更安静细腻的唱作实力，路人歌单却很少有它",
        "vsrc": "raw/broll_naxie.webm", "vstart": 11.0, "crop": TOUR_CROP, "delogo": None, "grade": "colorbalance=rs=-0.06:rm=-0.05:bm=0.10:bh=0.06",
        "asrc": "audio_src/woni_studio.wav", "chorus": 86.0, "show": 31.0, "bright": -0.33, "sat": 1.03,
    },
    {  # 1
        "key": "p1_ruguo", "no": "01",
        "name": "《如果你还爱我》", "plain": "如果你还爱我",
        "tag": "藏在专辑里的那桩心事",
        "note": "光良第一首完整词曲创作；还在等，却已感觉对方变冷",
        "vsrc": "raw/ruguo_full.webm", "vstart": None, "crop": "1390:880:0:0", "delogo": None, "grade": "",
        "asrc": None, "chorus": 218.0, "show": 34.0, "bright": -0.30, "sat": 1.06,
    },
]
