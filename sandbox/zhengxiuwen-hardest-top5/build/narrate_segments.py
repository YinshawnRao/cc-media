#!/usr/bin/env python3
"""Generate female narration wavs for the Sammi Cheng (郑秀文) hardest top 5 video."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = "zf_xiaoyi"
SR = 24000
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

BLOCKS = {
    "intro": "郑秀文，百变天后，舞台上的女王。但今天，我们不聊她有多红，只聊一件事——她的歌，到底有多难唱。这五首，有快有慢，有的考气场，有的考控制。先不排名，我们从第五名开始，一首一首听，她到底难在哪里。",
    "p5_moqi": "第五名，《默契》。它不靠炫技，听起来很顺，唱起来却很难。难在分寸：要唱出一段成熟感情里回望的味道，太平淡没有故事，太用力又会失去郑秀文那种利落、干净的都市感。粤语的咬字和音色，每一口都得拿捏得刚刚好。",
    "p4_buyao": "第四名，《不要惊动爱情》。它看起来很温柔，其实最考验控制，难点就在一个字——忍。气息要细，句尾要稳，情绪要有等待的感觉，不能唱成普通的苦情歌。越安静的歌越藏刀，唱坏了就是平，唱好了，才有把爱慢慢放进手心的那种力量。",
    "p3_zhide": "第三名，《值得》。这是郑秀文的第一张国语专辑，当年在台湾拿下销量冠军，连续六周登顶。它最容易被低估，难就难在长线条和情绪递进：主歌要收着，副歌要打开，却又不能变成硬喊。最难的是那两个字——值得，唱轻了没有信念，唱重了又容易俗。",
    "p2_zhongshen": "第二名，《终身美丽》。电影《瘦身男女》的主题曲，陈辉阳作曲，林夕填词，拿过金像奖最佳原创电影歌曲。它的难，不在飙高音，而在于每一句都要唱得漂亮、端正、真诚。副歌要有大歌的支撑，太轻没有力量，太重又会失去那份温柔。",
    "p1_shake": "第一名，《煞科》。它是《眉飞色舞》的粤语版，一首高强度的舞曲。难就难在——一边跳，一边唱，还要稳稳压住全场的女王气场。在这么快的节奏里，咬字、气息、律动一个都不能掉，少一口气，整段就垮了。能把它唱到游刃有余，才真的明白郑秀文有多强。",
    "outro": "再回顾一次这份榜单：第五《默契》，第四《不要惊动爱情》，第三《值得》，第二《终身美丽》，第一《煞科》。郑秀文最难的地方，从来不是某一个高音，而是她能在快歌里压住气场，在慢歌里收住情绪，把功夫稳稳地藏进每一个字里。",
    "outro_cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
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
