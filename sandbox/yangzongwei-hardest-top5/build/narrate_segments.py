#!/usr/bin/env python3
"""Generate female narration wavs for the Yang Zongwei hardest top 5 video."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "杨宗纬最难唱的五首歌，不是只看某一个高音点，而是看气息、声压、咬字和情绪，能不能在最脆弱的地方同时稳住。这期不提前公开完整榜单，我们从第五名往第一名听。",
    "p5_yueguoshanqiu": "第五名，《越过山丘》。这首不靠炸裂取胜，难在重量。李宗盛式的旋律和歌词，要求唱的人真的有时间感、沧桑感和自我回望。唱浅了像抒情，唱重了又会显得刻意。杨宗纬要把人生感唱出来，还不能把歌唱老。",
    "p4_liangliang": "第四名，《凉凉》。这首难在合唱分寸和古风气息。男声不是一个人独自爆发就行，而是要和女声形成互补：要稳、要厚、要收得住，还要撑出仙侠宿命感。多一点会抢，少一点又托不住整首歌。",
    "p3_yicijiuhao": "第三名，《一次就好》。它听起来温柔，但真唱很容易翻车。旋律线很长，气息要稳，情绪要有陪你去看天荒地老的画面感，却不能太用力煽情。越简单的句子，越考验声音的支撑和分寸。",
    "p2_qishidoumeiyou": "第二名，《其实都没有》。这首可怕在一个字：空。主歌要轻、稳、冷，像已经什么都没有了；副歌又要慢慢把情绪推开。唱轻了没故事，唱重了又会毁掉那种失重感。难的是让空荡感本身有重量。",
    "p1_yangcong": "第一名，《洋葱》。它的难点不是一个孤立高音，而是副歌连续递进太狠。那种一层一层剥开的旋律推进，对气息、声压和情绪控制要求都很高。主歌要压住卑微，副歌要打开，但不能唱成单纯哭喊。",
    "outro": "最后总结这期排名。第五《越过山丘》，第四《凉凉》，第三《一次就好》，第二《其实都没有》，第一《洋葱》。杨宗纬最难的地方，不是把悲伤唱大声，而是把脆弱、克制和爆发，放在同一条气息线上。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（见 tools/video/outro_cta.py / CONVENTIONS「固定结尾配音」）。
    "outro_cta": FIXED_OUTRO_CTA,
}


def trim_silence(audio: np.ndarray, threshold: float = 0.002, pad: int = 1800) -> np.ndarray:
    if audio.size == 0:
        return audio
    mono = audio if audio.ndim == 1 else audio.mean(axis=1)
    idx = np.where(np.abs(mono) > threshold)[0]
    if len(idx) == 0:
        return audio
    start = max(0, idx[0] - pad)
    end = min(len(audio), idx[-1] + pad)
    return audio[start:end]


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        audio = trim_silence(audio)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:18s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()

