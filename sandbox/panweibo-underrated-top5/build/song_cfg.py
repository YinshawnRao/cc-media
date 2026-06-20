#!/usr/bin/env python3
"""潘玮柏最被低估5首 — 单一配置源（clips.py 与 full_build.py 共用，防漂移）。

倒数揭晓顺序 5->1（列表即此序）。
- 同源曲（寂屋出租 / 机会 / 我们都怕痛 / 跟我走吧）：footage 窗 == 音乐窗（同源同窗 -> 口型同步），
  asrc=None；chorus 是该 MV 里副歌入点，footage 从 (chorus - pre) 切。
- 解耦曲（街头诗人）：该说唱专辑曲全网无官方 MV（B站只有粉丝"盗版MV"），用录音室音频(asrc)
  + 同专辑同期《反转地球》2007 官方 MV（1080p 修复）做 B-roll(vsrc)，两者独立；
  chorus 是录音室 hook 入点，vstart 是 B-roll 视频窗起点（任意干净段，不需对口型）。
全部 letterbox（crop 全宽横带去污染带后保留全宽，不放大）。
crop 去底部烧词/credit、机会顶 UP 水印；我们都怕痛顶 QQ音乐角标走全宽顶裁。
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

# 暗调/安静歌的音乐增益补偿（loudnorm 后仍偏低再抬）—— 实测：寂屋出租/机会 副歌偏轻
MGAIN = {"p5_jiwu": 1.26, "p4_jihui": 1.16}

# 封面/片尾背景底 = 《反转地球》2007 官方 MV 修复版（1080p，潘玮柏 headphones 特写）
COVER_SRC = "raw/fanzhuan_mv.mp4"
COVER_START = 115.0     # @115 潘玮柏 headphones 暖调特写，首帧作封面
COVER_LEN = 44.0
COVER_CROP = "1920:960:0:0"   # 去底部烧入字幕（字幕在 y978+，全宽裁底 118px）
COVER_DELOGO = None

INTRO_CLIP = "vert_cover"
OUTRO_CLIP = "vert_cover"

# 倒数 5 -> 1
SONGS = [
    {  # 5 寂屋出租 (零零七 2008) — 官方 MV(KTV版,底部大歌词) 同源
        "key": "p5_jiwu", "no": "05",
        "name": "《寂屋出租》", "plain": "寂屋出租",
        "tag": "藏在专辑中段的空房子",
        "note": "不靠大副歌，用孤独感慢慢铺开",
        "vsrc": "raw/jiwu_mv.mp4", "vstart": None, "crop": "720:330:0:0", "delogo": None, "grade": "",
        "asrc": None, "chorus": 172.0, "show": 30.0, "bright": -0.30, "sat": 1.04,
    },
    {  # 4 机会 (反转地球 2007, 南拳妈妈巨炮 + 方文山) — 720p MV 同源
        "key": "p4_jihui", "no": "04",
        "name": "《机会》", "plain": "机会",
        "tag": "他第一次唱抒情摇滚",
        "note": "南拳妈妈巨炮 × 方文山，转型期的特殊味道",
        "vsrc": "raw/jihui_mv.mp4", "vstart": None, "crop": "1280:632:0:44", "delogo": None,
        "grade": "colorbalance=rm=-0.05:bm=0.06",
        "asrc": None, "chorus": 183.0, "show": 30.0, "bright": -0.30, "sat": 1.05,
    },
    {  # 3 我们都怕痛 (808 2012) — 官方 MV(爱无限剧情)末段副歌潘玮柏特写 同源
        "key": "p3_paitong", "no": "03",
        "name": "《我们都怕痛》", "plain": "我们都怕痛",
        "tag": "最准的那次情绪克制",
        "note": "谁都怕受伤，所以谁都不敢先靠近",
        "vsrc": "raw/paitong_mv.mp4", "vstart": None, "crop": "640:280:0:80", "delogo": None,
        "grade": "colorbalance=rm=-0.04:bm=0.05",
        "asrc": None, "chorus": 188.0, "show": 30.0, "bright": -0.28, "sat": 1.05,
    },
    {  # 2 跟我走吧 (高手 2003, 林俊杰曲 + 徐世珍词) — 环球官方 MV 同源
        "key": "p2_genwo", "no": "02",
        "name": "《跟我走吧》", "plain": "跟我走吧",
        "tag": "嘻哈专辑里的温柔侧写",
        "note": "林俊杰谱曲、徐世珍填词的成熟情歌",
        "vsrc": "raw/genwo_mv.mp4", "vstart": None, "crop": "640:430:0:0", "delogo": None, "grade": "",
        "asrc": None, "chorus": 150.0, "show": 30.0, "bright": -0.30, "sat": 1.05,
    },
    {  # 1 街头诗人 (反转地球 2007, 中文 Rap) — 解耦：录音室音频 + 反转地球 MV B-roll
        "key": "p1_shiren", "no": "01",
        "name": "《街头诗人》", "plain": "街头诗人",
        "tag": "他真正想做的中文说唱",
        "note": "唱出一个做说唱的人，心里最真实的话",
        "vsrc": "raw/fanzhuan_mv.mp4", "vstart": 73.0, "crop": "1920:960:0:0", "delogo": None,
        "grade": "",
        "asrc": "audio_src/shiren.wav", "chorus": 96.0, "show": 34.0, "bright": -0.28, "sat": 1.06,
    },
]
