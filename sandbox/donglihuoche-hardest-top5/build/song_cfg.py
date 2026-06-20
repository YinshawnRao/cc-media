#!/usr/bin/env python3
"""动力火车最难5首 — 单一配置源（clips.py 与 full_build.py 共用，防漂移）。

倒数揭晓顺序 5->1（列表即此序）。每首 footage 窗 == 音乐窗（同源同窗 -> 口型同步）。
clip 从 (chorus - PRE) 切起，PRE = LEAD + 旁白时长 + 0.25 + DIG，使副歌正好落在满量展示段。
双人组合 -> 一律 letterbox（crop 传全宽横带，去污染带后保留全宽）。
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
TAIL_BUF = 3.0   # clip 末尾余量（clip_len = PRE + SHOW + TAIL_BUF）

# 暗调/安静歌的音乐增益补偿（loudnorm 后仍偏低再抬）
MGAIN = {"p3_wuqing": 1.18, "p4_beipan": 1.12}

INTRO_CLIP = "vert_mingtian"   # 封面/开场背景底（暗调 arena，文字易读）
OUTRO_CLIP = "vert_caihong"    # 片尾榜单背景底（巨蛋终场）

# 倒数 5 -> 1
SONGS = [
    {
        "key": "p5_chule", "no": "05",
        "name": "《除了爱你还能爱谁》", "plain": "除了爱你还能爱谁",
        "tag": "旋律线宽，一直逼着往上走",
        "note": "张雨生作曲；情绪浓、气息要稳，深情不能塌",
        "source": "raw/p5_chule_src.mp4", "chorus": 82.0, "show": 34.0,
        "crop": "1920:800:0:0", "mask": False,
    },
    {
        "key": "p4_beipan", "no": "04",
        "name": "《背叛情歌》", "plain": "背叛情歌",
        "tag": "前面铺、后面爆，整首绷住张力",
        "note": "从头到尾都不能松，情绪压满整首",
        "source": "raw/p4_beipan_live.mp4", "chorus": 232.0, "show": 32.0,
        "crop": "1920:852:0:92", "mask": False,
    },
    {
        "key": "p3_wuqing", "no": "03",
        "name": "《无情的情书》", "plain": "无情的情书",
        "tag": "爆发密度高，狠却不能只是吼",
        "note": "出道招牌难歌；一句接一句往上顶，气口短",
        "source": "raw/p3_wuqing_src.webm", "chorus": 193.0, "show": 34.0,
        "crop": "712:380:0:28", "mask": False,
    },
    {
        "key": "p2_caihong", "no": "02",
        "name": "《彩虹》", "plain": "彩虹",
        "tag": "副歌整段挂在高位，要一直撑住",
        "note": "悲壮、温柔、坚定压在同一条旋律里",
        "source": "raw/p2_caihong_live.mp4", "chorus": 226.0, "show": 36.0,
        "crop": "1920:1080:0:0", "mask": False,
    },
    {
        "key": "p1_mingtian", "no": "01",
        "name": "《明天的明天的明天》", "plain": "明天的明天的明天",
        "tag": "动力火车难度的天花板",
        "note": "近七分钟全程高压，双人和声+尾段拼体能",
        "source": "raw/p1_mingtian_src.mp4", "chorus": 256.0, "show": 44.0,
        "crop": "1920:900:0:0", "mask": False,   # 裁底部烧字幕(源 y~915-975)
    },
]
