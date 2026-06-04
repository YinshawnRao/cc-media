#!/usr/bin/env python3
"""Generate female narration wavs for Angela Zhang variety-show TOP5."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
AUDIO = ROOT / "audio"
AUDIO.mkdir(exist_ok=True)

PY = REPO / "tools" / "tts" / "venv" / "bin" / "python"
NARRATE = REPO / "tools" / "tts" / "narrate.py"

VOICE = "zf_xiaoyi"
SPEED = "1.04"

BLOCKS = {
    "intro": (
        "今天这期，按代表性和舞台记忆点，盘张韶涵的综艺歌曲TOP5。"
        "不排原唱金曲，只看音综和综艺舞台。"
        "从重新被看见的《阿刁》，到温柔收尾的《念念》，听她怎样把清亮的声音，唱出锋利、开阔和生命力。"
    ),
    "p1_adiao": (
        "第一首，《阿刁》。如果只选一首张韶涵最具代表性的综艺翻唱，这一版基本绕不开。"
        "它厉害的不只是高音够亮，而是她把原曲里的倔强、孤独和反击感，唱成了自己的故事。"
        "那种我偏要往上走的生命力，几乎和她本人的经历重叠在一起。"
    ),
    "p2_star": (
        "第二首，《夜空中最亮的星》。这一版很有后期综艺舞台的成熟感。"
        "张韶涵的声音本来就清亮、有穿透力，放进这种大旋律作品里，会天然放大坚定和向上的气质。"
        "如果《阿刁》是锋利的反击，这首就是把力量唱得更开阔。"
    ),
    "p3_burn": (
        "第三首，《燃烧》。这是一版很值得考古的老舞台。"
        "它没有后来《歌手2018》那种全民讨论度，但现场完成度很高，能听到她早期音综里更直接、更用力的一面。"
        "不是靠故事加成，而是靠现场硬撑起来的爽感。"
    ),
    "p4_rooftop": (
        "第四首，《屋顶》。这一版的看点不在爆发，而在氛围。"
        "作为男女合唱舞台，张韶涵没有急着压过歌曲，而是把声音放得更柔，保留旋律里的暧昧和青春感。"
        "放在这组榜单里，它像一次中场换气，耐听、舒服，也很有画面。"
    ),
    "p5_niannian": (
        "第五首，《念念》。它更像粉丝向的惊喜，不是大众记忆里最强出圈的舞台。"
        "但它的好处在于旋律清爽、情绪轻盈，能听到张韶涵温柔又明亮的一面。"
        "前面几首负责大舞台和大情绪，这首适合做一个干净的收尾。"
    ),
    "outro": (
        "这就是我心里的张韶涵综艺歌曲TOP5。"
        "她当然会唱希望，也会唱光，但更难得的是，她能把倔强、孤独、开阔和温柔，都唱成自己的辨识度。"
        "你觉得还有哪一个综艺舞台，应该挤进这份榜单？"
    ),
}


def wav_duration(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "r")) as wav:
        return round(wav.getnframes() / wav.getframerate(), 3)


def main() -> int:
    meta = {}
    for key, text in BLOCKS.items():
        out = AUDIO / f"{key}.wav"
        subprocess.run(
            [str(PY), str(NARRATE), text, "--voice", VOICE, "--speed", SPEED, "-o", str(out)],
            check=True,
            cwd=str(REPO),
        )
        meta[key] = {
            "text": text,
            "dur": wav_duration(out),
            "voice": VOICE,
            "speed": float(SPEED),
        }
        print(f"{key:12s} {meta[key]['dur']:6.2f}s")

    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("total narration", round(sum(item["dur"] for item in meta.values()), 2), "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
