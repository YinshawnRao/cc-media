#!/usr/bin/env python3
"""Central Qwen-TTS batch template for multi-segment narration.

Edit BLOCKS to match the project manifest. Voice selection is resolved once at project start and read from
voice-selection.json. New projects call this central Qwen entrypoint without a VOICE constant.
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
    "p1_pandora": "第五名，《潘朵拉》。明亮嗓音，也能唱出神秘感。",
    "p2_nahan": "第四名，《呐喊》。亮嗓也有尖锐的一面。",
    "p3_pojian": "第三名，《破茧》。高音推动了整首歌的力量。",
    "p4_quanmian": "第二名，《全面沦陷》。克制里，也能听见失控。",
    "p5_adiao": "第一名，《阿刁》。这次翻唱，唱出了倔强。",
    # 默认避免重复互动；本期可通过 editorial 修改或省略 CTA。
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
