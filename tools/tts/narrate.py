#!/usr/bin/env python3
"""
cc-media 本地中文配音 (Kokoro + misaki[zh])。

默认男声 zm_yunxi；女声 zf_xiaoyi 仅在明确要求时用 (--voice zf_xiaoyi 或 --female)。
其余 Kokoro 中文音色仍可通过 --voice 显式指定，但不作为默认。

用法:
    venv/bin/python narrate.py "要配音的中文文本" -o out.wav
    venv/bin/python narrate.py script.txt --female -o out.wav
    venv/bin/python narrate.py "文本" --voice zf_xiaoni --speed 1.1 -o out.wav
"""
import argparse
import sys
from pathlib import Path

DEFAULT_MALE = "zm_yunxi"     # 默认
DEFAULT_FEMALE = "zf_xiaoyi"  # 仅在要求女声时
SAMPLE_RATE = 24000
# benchmark 跑通的全部中文音色，供显式选择
CHINESE_VOICES = [
    "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi",
    "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang",
]


def main() -> int:
    p = argparse.ArgumentParser(description="cc-media 本地中文配音 (Kokoro + misaki[zh])")
    p.add_argument("input", help="要配音的中文文本，或 .txt 文件路径")
    p.add_argument("-o", "--output", required=True, help="输出 wav 路径")
    p.add_argument("--voice", default=None,
                   help=f"音色 ID（默认 {DEFAULT_MALE}）。可选: {', '.join(CHINESE_VOICES)}")
    p.add_argument("--female", action="store_true",
                   help=f"用默认女声 {DEFAULT_FEMALE}（等价 --voice {DEFAULT_FEMALE}）")
    p.add_argument("--speed", type=float, default=1.0, help="语速倍率（默认 1.0）")
    args = p.parse_args()

    # 音色决策：--voice 显式 > --female > 默认男声
    if args.voice:
        voice = args.voice
    elif args.female:
        voice = DEFAULT_FEMALE
    else:
        voice = DEFAULT_MALE

    # 文本来源：文件路径或直接字面量
    maybe = Path(args.input)
    text = maybe.read_text(encoding="utf-8").strip() if maybe.is_file() else args.input
    if not text:
        print("error: 文本为空", file=sys.stderr)
        return 1

    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="z")
    chunks = [audio for _, _, audio in pipeline(text, voice=voice, speed=args.speed)]
    if not chunks:
        print("error: 未生成音频", file=sys.stderr)
        return 1
    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, audio, SAMPLE_RATE)
    print(f"wrote {out}  voice={voice} speed={args.speed} dur={len(audio)/SAMPLE_RATE:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
