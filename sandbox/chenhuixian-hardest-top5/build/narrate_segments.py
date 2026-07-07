#!/usr/bin/env python3
"""Male narration for 陈慧娴最难的5首歌.

Countdown 5 -> 1 (#1 = 月亮, the climax). 倒数揭晓。
事实口径（已核实）：
- 千千阙歌 / 夜机 = 1989 专辑《永远是你的朋友》（宝丽金，七白金，告别专辑）。
- 月亮 / 飘雪 / 归来吧 = 1992 专辑《归来吧》（陈慧娴美国念书期录制，缺席宣传仍很成功）。
- 不臆测词曲创作者（brief 未要求，避免出错）；只讲已核实的专辑/年份与演唱难度。
外文/英文一律不进配音（Kokoro 中英混读差），只进屏幕字幕。
固定结尾 CTA 由 tools/video/outro_cta.py 提供，永远是最后一句（防双 CTA：outro 不再带投票问句）。
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
sys.path.insert(0, str(ROOT.parents[1] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zm_yunxi"
SR = 24000

BLOCKS = {
    "intro": "提到陈慧娴，很多人第一个想到的，是《千千阙歌》里那句，来日纵使千千阙歌。但她真正难的地方，从来不是飙多高的音，而是那种又轻、又稳、又体面的唱法。今天我们从第五名倒数，盘一盘陈慧娴最难的五首歌。",
    "p5_guilai": "第五名，《归来吧》。它是一九九二年同名专辑《归来吧》的主打，而这张专辑，是陈慧娴在美国念书的时候录的，几乎缺席了所有宣传，却照样卖得很好。这首歌难就难在，它要唱出归来那种开阔和坚定，是一首很大气的歌；可一旦用力过头，就会变成扯着嗓子喊口号。陈慧娴的歌最怕情绪过量，这首尤其考验声音的端正、气息的支撑，还有那种收着唱、却依然有力量的分寸。",
    "p4_yeji": "第四名，《夜机》。它收在一九八九年那张《永远是你的朋友》里，和《千千阙歌》是同一张专辑。这首歌的难，在于平衡。主歌是中低音的叙事，唱的是一个人坐着夜班飞机离开的孤独，太平了没情绪，太满了又出戏；到了副歌，再一点点把情绪打开。粤语的咬字、换气的气口、情绪一层一层往上推，全都得稳。唱不好，夜机就会变成一班晚点的航班。",
    "p3_piaoxue": "第三名，《飘雪》。它同样来自《归来吧》这张专辑，也是当年很流行的一首。它最难的地方，是那种冷。不能只把它唱成伤心，而要唱出雪落下来的那种轻、那种冷、那种慢。音准要干净，气息要细，尾音收得稍微一脏，整首歌的孤清感就没了。普通人唱，很容易唱成一首普通的苦情歌；陈慧娴唱，才有那种一个人站在雪夜里的清冷。",
    "p2_qianqian": "第二名，《千千阙歌》。这首太红了，红到很多人忘了，它其实很难。它的难，不在某一个高音，而在整首歌的耐力。前面要温柔地回望，像在跟一段时光好好告别；后面要一步一步，推到那个万人合唱的大场面。副歌用力一点就俗，再收一点又撑不起这份经典。真正难的，是唱出离别、但不狼狈的那份体面。",
    "p1_yueliang": "第一名，《月亮》。它和《飘雪》《归来吧》一样，都收在《归来吧》那张专辑里。把它放在第一，是因为它几乎集齐了陈慧娴所有最难的东西：长长的旋律线、大段的弱声、还有对气息和高位的极致要求。它不能唱得太重，一重，月光的感觉就没了；也不能太虚，一虚，声音就失去了支点。副歌要有一点明亮的推力，可整体又得清冷、克制、优雅。这是一首典型的、越轻越难的歌，也是我心里，陈慧娴最难的那一首。",
    "outro": "五首歌盘完。第五，归来吧；第四，夜机；第三，飘雪；第二，千千阙歌；第一，月亮。你会发现，陈慧娴最难的歌，几乎都不靠飙高音取胜，而是赢在那种又轻、又稳、又体面的控制力。她真正厉害的地方，是把最汹涌的情绪，唱得云淡风轻。",
    "outro_cta": FIXED_OUTRO_CTA,
}


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="z")
    meta = {}
    for key, text in BLOCKS.items():
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        out = AUDIO / f"{key}.wav"
        sf.write(out, audio, SR)
        meta[key] = {"text": text, "dur": round(len(audio) / SR, 3)}
        print(f"{key:14s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
