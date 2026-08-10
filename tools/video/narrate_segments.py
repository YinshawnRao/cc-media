#!/usr/bin/env python3
"""Central-TTS batch template for multi-segment narration.

Edit BLOCKS only. Voice selection is resolved once at project start and read from
voice-selection.json. New projects must not add a VOICE constant or import Kokoro.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TTS = REPO_ROOT / "tools" / "tts" / "narrate.py"
SELECTION = Path("voice-selection.json")
REQUEST = Path("narration-request.json")
OUTPUT_DIR = Path("audio")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outro_cta import FIXED_OUTRO_CTA


BLOCKS = {
    "intro": "很多人记住张韶涵，是因为《隐形的翅膀》。她好像一直是那个唱希望、唱光、唱梦想的天使嗓音。但如果你只记得这一面，可能真的低估了她。因为张韶涵的歌里，也藏着一个更暗、更燃、更有攻击性的世界。",
    "p1_pandora": "第五名《潘朵拉》。这首歌很适合打开张韶涵的另一面。它不是《隐形的翅膀》那种明亮的希望，而像一个被打开的魔盒，电子摇滚、童话感、神秘感混在一起，清亮声线突然变得很有戏剧张力。",
    "p2_nahan": "第四名《呐喊》。张韶涵最特别的地方，是她的声音明明很亮，却可以唱出一种尖锐的冲击力。这首不是治愈你，而是把压住的情绪直接撕开。",
    "p3_pojian": "第三名《破茧》。这首是张韶涵战斗系的一面。它不是简单励志，而是从噩梦、深渊、撕裂感里往外冲。她的高音在这里不是漂亮，而是像一道直接破开的光。",
    "p4_quanmian": "第二名《全面沦陷》。这首歌的气质很不一样，它不是张韶涵常见的清澈明亮，而是更暗、更沉、更有失控感。她把沦陷唱得不是软弱，而像明知道危险，还是要往里走。",
    "p5_adiao": "第一名《阿刁》。这首不是她自己的原唱作品，但它几乎把张韶涵的生存感唱出来了。她不是在扮演坚强，而是真的把瘦小身体里的倔强、孤独和反击，全部推到了舞台最前面。",
    # 作品自身 outro 不写第二个投票问句；互动统一交给固定 CTA。
    "outro": "所以张韶涵不是只有《隐形的翅膀》。她当然会唱希望，但她更厉害的地方，是能把黑暗、挣扎、破碎和反击，都唱成一种往上飞的力量。",
    # 必须和本期其他旁白使用同一 voice-selection.json。
    "outro_cta": FIXED_OUTRO_CTA,
}


def main() -> int:
    if not SELECTION.is_file():
        raise SystemExit(
            "missing voice-selection.json; resolve the original task brief before narration"
        )
    request = {
        "blocks": [
            {
                "id": key,
                "text": text,
                "output": str(OUTPUT_DIR / f"{key}.wav"),
            }
            for key, text in BLOCKS.items()
        ]
    }
    REQUEST.write_text(
        json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    subprocess.run(
        [
            sys.executable,
            str(TTS),
            "--batch",
            str(REQUEST),
            "--selection-file",
            str(SELECTION),
        ],
        check=True,
    )

    meta = {}
    for key, text in BLOCKS.items():
        wav = OUTPUT_DIR / f"{key}.wav"
        sidecar = wav.with_suffix(wav.suffix + ".tts.json")
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        meta[key] = {
            "text": text,
            "dur": round(record["wav"]["duration_seconds"], 3),
            "voice_id": record["resolved_voice_id"],
            "tts_sidecar": str(sidecar),
        }
    Path("narration.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"TOTAL narration {sum(item['dur'] for item in meta.values()):.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
