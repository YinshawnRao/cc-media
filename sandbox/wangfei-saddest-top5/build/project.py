from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
CLIPS = ROOT / "clips"

LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
CTA_GAP = 1.0
OUTRO_TAIL = 1.8
VOCAL_UNDER_NARRATION = 2.0

TITLE = "王菲最苦的5首歌"
SLUG = "wangfei-saddest-top5"

ITEMS = [
    {
        "key": "aimei",
        "raw": "raw/aimei_bili_seedvr.mp4",
        "bvid": "BV1BdRZBaEJC",
        "no": "05",
        "name": "《暧昧》",
        "plain": "暧昧",
        "year": "1995",
        "show": 55.0,
        "vocal_onset": 177.17,
        "crop": "1620:980:0:80",
        "br": "-0.24",
        "sat": "1.05",
        "tag": "没有身份，所以连难过都悬着",
        "note": "说不清，等不到，退不掉，关系不上不下。",
    },
    {
        "key": "youchai",
        "raw": "raw/youchai_bili_live1080.mp4",
        "bvid": "BV1Zq4y1E7C8",
        "no": "04",
        "name": "《邮差》",
        "plain": "邮差",
        "year": "1999",
        "show": 34.0,
        "vocal_onset": 63.88,
        "crop": "1440:1080:0:0",
        "br": "-0.30",
        "sat": "1.02",
        "tag": "已经知道答案，却还想再等一等",
        "note": "等过，盼过，也替对方找过理由。",
    },
    {
        "key": "qizi",
        "raw": "raw/qizi_bili_4kfix.mp4",
        "bvid": "BV1bR4y157rD",
        "no": "03",
        "name": "《棋子》",
        "plain": "棋子",
        "year": "1994",
        "show": 36.0,
        "vocal_onset": 200.09,
        "crop": "1920:900:0:0",
        "br": "-0.28",
        "sat": "1.06",
        "tag": "清醒地发现自己没有主动权",
        "note": "想走出控制，却只是换了一个格子。",
    },
    {
        "key": "xiaowangshu",
        "raw": "raw/xiaowangshu_bili_betacam.mp4",
        "bvid": "BV14ksteLEgN",
        "no": "02",
        "name": "《笑忘书》",
        "plain": "笑忘书",
        "year": "2000",
        "show": 42.0,
        "vocal_onset": 95.11,
        "crop": "1440:1080:0:0",
        "br": "-0.28",
        "sat": "1.04",
        "tag": "试图说服自己：算了吧",
        "note": "时间爬过身体，痕迹只有自己知道。",
    },
    {
        "key": "anyong",
        "raw": "raw/anyong_bili_1080fix.mp4",
        "bvid": "BV1pg411K7yb",
        "no": "01",
        "name": "《暗涌》",
        "plain": "暗涌",
        "year": "1997",
        "show": 42.0,
        "vocal_onset": 160.57,
        "crop": "1440:660:0:0",
        "br": "-0.34",
        "sat": "1.04",
        "tag": "还没失去，已经听见坍塌",
        "note": "表面风平浪静，心里早就翻江倒海。",
    },
]

RANKING_ROWS = [
    ("01", "暗涌"),
    ("02", "笑忘书"),
    ("03", "棋子"),
    ("04", "邮差"),
    ("05", "暧昧"),
]
