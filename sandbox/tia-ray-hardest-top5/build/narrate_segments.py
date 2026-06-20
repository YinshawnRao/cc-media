#!/usr/bin/env python3
"""Generate female Chinese narration wavs for 袁娅维最难5首歌."""

import json
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO / "tools" / "video"))

import song_cfg as cfg
from outro_cta import FIXED_OUTRO_CTA

OUT = ROOT / "audio"
OUT.mkdir(parents=True, exist_ok=True)

BLOCKS = {
    "intro": "袁娅维的难，不只是高音。是律动、转音、英文咬字、情绪和声压，同时在线。今天倒数盘她最难的五首歌，先从第五名开始。",
    "p5_achu": "第五名，《阿楚姑娘》。它不是炫技型难歌，难在朴素里还要有厚度。声音要干净，故事要立住，灵魂乐的颗粒感又不能把民谣底色唱脏。",
    "p4_chuntian": "第四名，《开往春天的地铁》。这首难在改编感和气息线。前面不能满，后面要慢慢推开，还要唱出爵士化的流动感。",
    "p3_lvxing": "第三名，《旅行中忘记》。这首听起来松，其实每一句都在控制。groove、气口、转音都要像呼吸一样自然；唱直了没灵魂，唱油了又过火。",
    "p2_biefeihua": "第二名，《别废话》。它要的是态度、节奏和声压。唱得拽，但不能乱；爆发要狠，但不能粗。R and B 和 funk 的律动一歪，整首马上塌。",
    "p1_starfall": "第一名，《Star fall》。难点是大动态、高位爆发、华丽转音和英文咬字一起上。它不是喊上去就赢，而是要又强又准，还要有袁娅维那种灵魂乐弹性。",
    "outro": "这五首难歌，其实刚好说明袁娅维的核心。她不是只会飙，而是能把技术、律动和情绪，同时唱成一个整体。真正难的是，听起来还很自由。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def wav_dur(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return round(handle.getnframes() / handle.getframerate(), 3)


def main():
    meta = {}
    tool = REPO / "tools" / "tts" / "narrate.py"
    for key, text in BLOCKS.items():
        txt = OUT / f"{key}.txt"
        wav = OUT / f"{key}.wav"
        txt.write_text(text, encoding="utf-8")
        subprocess.run(
            [
                str(REPO / "tools" / "tts" / "venv" / "bin" / "python"),
                str(tool),
                str(txt),
                "--female",
                "--speed",
                "1.08",
                "-o",
                str(wav),
            ],
            check=True,
            cwd=REPO,
        )
        meta[key] = {"text": text, "duration": wav_dur(wav)}
        print(f"{key}: {meta[key]['duration']}s")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
