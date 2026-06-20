#!/usr/bin/env python3
"""袁娅维最难5首歌 — single source of timeline/source truth."""

LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.05
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
TAIL_BUF = 2.5

INTRO_CLIP = "vert_starfall"
OUTRO_CLIP = "vert_lvxing"

MGAIN = {
    "p5_achu": 1.08,
    "p4_chuntian": 1.10,
    "p3_lvxing": 1.05,
}

SONGS = [
    {
        "key": "p5_achu",
        "no": "05",
        "name": "《阿楚姑娘》",
        "spoken_name": "《阿楚姑娘》",
        "plain": "阿楚姑娘",
        "tag": "民谣底色里，放进灵魂乐厚度",
        "note": "干净、真诚、有故事，还不能唱成普通抒情翻唱",
        "source": "raw/p5_achu_singer.mp4",
        "vocal_start": 140.8,
        "show": 31.0,
        "crop": "420:360:300:60",
        "delogo": "165:25:235:175",
        "delogo_enable": "between(t,15.0,20.5)+between(t,38.0,44.0)",
    },
    {
        "key": "p4_chuntian",
        "no": "04",
        "name": "《开往春天的地铁》",
        "spoken_name": "《开往春天的地铁》",
        "plain": "开往春天的地铁",
        "tag": "改编感、气息线、城市流动感",
        "note": "前面要收，后面慢慢推开，太平和太满都不对",
        "source": "raw/p4_chuntian.mp4",
        "vocal_start": 87.8,
        "show": 26.0,
        "crop": "780:720:640:110",
    },
    {
        "key": "p3_lvxing",
        "no": "03",
        "name": "《旅行中忘记》",
        "spoken_name": "《旅行中忘记》",
        "plain": "旅行中忘记",
        "tag": "听起来松，里面全是控制",
        "note": "groove、转音、气口都要像呼吸一样自然",
        "source": "raw/p3_lvxing.mp4",
        "vocal_start": 105.4,
        "show": 31.0,
        "crop": "1080:820:420:80",
    },
    {
        "key": "p2_biefeihua",
        "no": "02",
        "name": "《别废话》",
        "spoken_name": "《别废话》",
        "plain": "别废话",
        "tag": "态度、节奏、声压一起走钢丝",
        "note": "唱得拽但不能乱，爆发要狠但不能粗",
        "source": "raw/p2_biefeihua.mp4",
        "vocal_start": 39.7,
        "show": 29.0,
        "crop": "1280:820:640:70",
    },
    {
        "key": "p1_starfall",
        "no": "01",
        "name": "《Starfall》",
        "spoken_name": "《Star fall》",
        "plain": "Starfall",
        "tag": "大动态、高位爆发、华丽转音",
        "note": "不是喊上去就赢，而是又强又准，还要有灵魂乐弹性",
        "source": "raw/p1_starfall.mp4",
        "vocal_start": 206.8,
        "show": 38.0,
        "crop": "1040:760:440:90",
    },
]
