#!/usr/bin/env python3
"""Generate FEMALE narration wavs for 林俊杰最被低估的5首歌 (countdown 5->1).

Hard rules (see design.md / CONVENTIONS):
- Female voice zf_xiaoyi (brief explicitly asks 女性配音).
- All five titles are pure Chinese (距离 / 不流泪的机场 / 突然累了 / 陌生老朋友 / 黑键) so TTS may
  speak them — no CN-EN mixing problem this time.
- Intro must NOT reveal the ranking. Outro reveals the full ranking (screen + voice).
- outro = work's own summary/升华 (no vote question — anti double-CTA).
- outro_cta = FIXED_OUTRO_CTA, verbatim, the LAST line of the whole video (hard constraint,
  single source tools/video/outro_cta.py; brief may not override).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
from outro_cta import FIXED_OUTRO_CTA  # noqa: E402

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "提到林俊杰，很多人先想到的，是江南、可惜没如果这些传唱度最高的歌。但真正让歌迷反复单曲循环的，往往是那些被主打盖过、却写得极好的遗珠。今天这五首，我们先不公布完整排名，从第五名开始，一首一首慢慢听。",
    # 5 《黑键》— 新地球 2014，黑暗三部曲终章
    "p5_heijian": "第五名，《黑键》。它是黑暗三部曲的最终章，阿信填词，林俊杰自己谱曲。比起黑武士、黑暗骑士的戏剧感，这首更像他写给自己音乐道路的一封信。它没有可惜没如果那样的传唱度，音乐性和叙事感却很强，尤其黑键、白键那组意象，最适合真爱粉细细品。",
    # 4 《陌生老朋友》— 学不会 2011，林夕词
    "p4_moshen": "第四名，《陌生老朋友》。它藏在《学不会》这张专辑里，被那些你很冒险的梦这样的歌盖过，很容易被路人跳过。可它的概念特别好：明明曾经那么熟，后来却变成了最懂彼此的陌生人。林夕写这种关系里的残影，一出手，就像一份老伤口的复查报告。",
    # 3 《突然累了》— 编号89757 2006
    "p3_turan": "第三名，《突然累了》。在《编号八九七五七》里，它被一千年以后、被风吹过的夏天这些强势作品盖过，显得没那么抢耳。但它的好，正在于不抢。唱的不是失恋到崩溃，而是那种突然就撑不住的疲惫。林俊杰早期这点灰色气质，很值得回过头来重听。",
    # 2 《不流泪的机场》— 西界 2005
    "p2_jichang": "第二名，《不流泪的机场》。在《西界》里，它的存在感远不如杀手、发现爱。可这首歌的画面感特别强：机场、离开、忍住不哭。它不是把悲伤唱爆，而是把那一声再见，死死压在喉咙里。后来在巡演里，他又重新唱起它，也说明在歌迷心里，它从不是一首普通的冷门歌。",
    # 1 《距离》— 第二天堂 2004
    "p1_juli": "第一名，《距离》。它来自《第二天堂》，同一张专辑里有江南、有豆浆油条，于是《距离》一直像被压在专辑后半的遗珠。但它的旋律线非常完整，情绪也很早期林俊杰。不是大开大合的苦情，而是那种想靠近、又始终隔着一点点的酸。放到现在听，反而比很多主打更耐嚼。",
    # outro = 内容总结 + 主题升华（不带投票问句，互动交给固定 CTA）
    "outro": "这就是这一期，林俊杰最被低估的五首歌。从第五到第一：《黑键》、《陌生老朋友》、《突然累了》、《不流泪的机场》，还有《距离》。它们没有最高的传唱度，却藏着他最细腻的那一面。林俊杰最动人的，从来不只是高音和技巧，而是这些被低估的歌里，那份说不出口的少年心事。",
    # 固定引流 CTA：全片最后一句，逐字固定，禁改（tools/video/outro_cta.py / CONVENTIONS）。
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
        print(f"{key:12s} {meta[key]['dur']:6.2f}s  {out}")
    (ROOT / "narration.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL narration", round(sum(item["dur"] for item in meta.values()), 2), "s")


if __name__ == "__main__":
    main()
