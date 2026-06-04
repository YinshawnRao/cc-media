#!/usr/bin/env python3
import json
import subprocess
import wave
import contextlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
AUDIO.mkdir(exist_ok=True)

NARRATE = Path("/Users/yinshawnrao/explorer/cc-media/tools/tts/narrate.py")
PY = Path("/Users/yinshawnrao/explorer/cc-media/tools/tts/venv/bin/python")
VOICE = "zm_yunxi"
SPEED = "1.06"

BLOCKS = [
    ("intro", "孙楠唱过很多版《拯救》，但真正能打进神级现场的，其实没那么多。音准、气息、高音质量、现场压力、情绪推进，这次我们按演唱完成度排，只看现场，不看情怀滤镜。"),
    ("p5_chinastar", "第五名，给《中国之星》版。这一版的优势不是最原始的声压，而是编曲规格和竞演完成度。弦乐、乐队、舞台层次都更现代，孙楠的高音也依然足够有压迫感。"),
    ("p4_korea2002", "第四名，2002第四届中韩歌会。这一版的孙楠非常年轻，声音状态很冲，副歌一出来就是典型的早期孙楠：亮、硬、穿透力强，几乎不跟你讲道理。"),
    ("p3_changchun2003", "第三名，2003现场版。相比2002那种直接往前冲，这一版的完成度更完整。主歌铺垫、副歌爆发、尾音处理都更成熟，声音一出来就有一种内地一哥的压场感。"),
    ("p2_singer2024", "第二名，《歌手2024》直播版。这一版最厉害的地方，不只是唱得稳，而是现场压力太大：直播、竞技、全网围观，孙楠还要在55岁的状态下把这首歌重新唱回来。它未必是机能最巅峰的一版，但绝对是最有话题价值、也最适合传播的一版。"),
    ("duel", "一个是55岁直播证明自己，一个是巅峰期原Key标准答案。真正难选的，其实是第二和第一之间的这一点差距。"),
    ("p1_korea5", "第一名，第五届中韩歌会原Key版。这一版几乎是孙楠《拯救》现场里的标准答案：原Key、强声、高音、稳定度、舞台气场，全都在线。最恐怖的是，它不是靠单个高音撑起来，而是从主歌开始就一直在蓄力，副歌出来以后，声音又亮又厚，尾音还能收得住。"),
    ("outro", "如果看传播，《歌手2024》版可能最有爽感；但如果只看巅峰机能和现场完成度，第五届中韩歌会版，确实太难超了。你心中的《拯救》最强Live是哪一版？评论区开麦，但别比孙楠还大声。"),
]


def duration(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "r")) as wav:
        return round(wav.getnframes() / wav.getframerate(), 3)


items = []
for key, text in BLOCKS:
    out = AUDIO / f"{key}.wav"
    subprocess.run(
        [str(PY), str(NARRATE), text, "--voice", VOICE, "--speed", SPEED, "-o", str(out)],
        check=True,
    )
    items.append({"key": key, "text": text, "duration": duration(out)})

(ROOT / "narration.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(items, ensure_ascii=False, indent=2))
