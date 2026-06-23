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

TITLE = "陈奕迅最苦的5首歌"
SLUG = "eason-saddest-top5"

ITEMS = [
    {
        "key": "putao",
        "raw": "raw/putao.mp4",
        "bvid": "BV1sE411c7Cy",
        "no": "05",
        "name": "《葡萄成熟时》",
        "plain": "葡萄成熟时",
        "year": "2005",
        "show": 34.0,
        "vocal_onset": 193.24,
        "crop": "1920:900:0:0",
        "br": "-0.28",
        "sat": "1.06",
        "tag": "痛也要等它成熟",
        "note": "它不急着劝你别痛，而是把遗憾熬成时间本身。",
    },
    {
        "key": "sunyou",
        "raw": "raw/sunyou.mp4",
        "bvid": "BV1qS4y1S7BN",
        "no": "04",
        "name": "《最佳损友》",
        "plain": "最佳损友",
        "year": "2006",
        "show": 31.0,
        "vocal_onset": 61.11,
        "crop": "1902:1080:0:0",
        "br": "-0.30",
        "sat": "1.04",
        "tag": "友情走散，比失恋更难说",
        "note": "没有分手仪式，也没有一句正式告别，只剩越来越少的联系。",
    },
    {
        "key": "renlai",
        "raw": "raw/renlai_live.mp4",
        "bvid": "BV1F34y177xc",
        "no": "03",
        "name": "《人来人往》",
        "plain": "人来人往",
        "year": "2002",
        "show": 42.0,
        "vocal_onset": 130.82,
        "crop": "1920:620:0:180",
        "br": "-0.30",
        "sat": "1.05",
        "tag": "世界热闹，留下的人很少",
        "note": "它不只写爱情，也写所有关系最终都会流动。",
    },
    {
        "key": "mingnian",
        "raw": "raw/mingnian.mp4",
        "bvid": "BV1T3411T7RN",
        "no": "02",
        "name": "《明年今日》",
        "plain": "明年今日",
        "year": "2002",
        "show": 40.0,
        "vocal_onset": 120.42,
        "crop": "2470:930:0:0",
        "br": "-0.30",
        "sat": "1.04",
        "tag": "把没有你的余生都想完",
        "note": "最狠的不是分别，而是你已经看见未来没有自己。",
    },
    {
        "key": "fushi",
        "raw": "raw/fushi_alt_dual.mp4",
        "bvid": "BV1LNsbe8ECx",
        "no": "01",
        "name": "《富士山下》",
        "plain": "富士山下",
        "year": "2006",
        "show": 32.0,
        "vocal_onset": 184.04,
        "crop": "1920:900:0:0",
        "br": "-0.34",
        "sat": "1.02",
        "tag": "放下，是爱而不得的最高级",
        "note": "爱不是把山搬走，而是终于承认自己该离开。",
    },
]

RANKING_ROWS = [
    ("01", "富士山下"),
    ("02", "明年今日"),
    ("03", "人来人往"),
    ("04", "最佳损友"),
    ("05", "葡萄成熟时"),
]

