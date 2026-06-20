#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Hua Chenyu hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 38.0
# 寒鸦：副歌连唱段 src228-258 后接器乐 gap，且 src225.5-227.4 有一段戏剧停顿——
# 把停顿藏进旁白、展示段只取无静音的连唱段 → SHOW 缩到 28（见 CONVENTIONS 展示段硬规则 C）。
SHOW_MAP = {"p3_hanya": 28.0}
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
# 齐天源整体偏轻(母带 ~-27dB)，loudnorm 已抬到 -14；如成片仍偏轻在此微调。
MGAIN = {"p2_douniu": 0.9, "p4_woguanni": 1.35}
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0   # outro 升华 → 固定 CTA 的消化位（见 CONVENTIONS「固定结尾配音」）


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

items = [
    {
        "key": "p5_yanhuo",
        "clip": "vert_yanhuo",
        "no": "05",
        "name": "《烟火里的尘埃》",
        "plain": "烟火里的尘埃",
        "tag": "安静比爆发更难唱稳",
        "note": "弱声、气息线、真假声边缘",
        "mask": False,
    },
    {
        "key": "p4_woguanni",
        "clip": "vert_woguanni",
        "no": "04",
        "name": "《我管你》",
        "plain": "我管你",
        "tag": "摇滚爆发拼的是体能",
        "note": "声压、态度、稳定性都要在线",
        "mask": False,
    },
    {
        "key": "p3_hanya",
        "clip": "vert_hanya",
        "no": "03",
        "name": "《寒鸦少年》",
        "plain": "寒鸦少年",
        "tag": "全程冷峻锋利不松劲",
        "note": "穿透力、咬字、持续向上",
        "mask": False,
    },
    {
        "key": "p2_douniu",
        "clip": "vert_douniu",
        "no": "02",
        "name": "《斗牛》",
        "plain": "斗牛",
        "tag": "唱完像打完一场比赛",
        "note": "节奏密、推进猛、还要控制",
        "mask": False,
    },
    {
        "key": "p1_qitian",
        "clip": "vert_qitian",
        "no": "01",
        "name": "《齐天》",
        "plain": "齐天",
        "tag": "华晨宇难度的天花板",
        "note": "吟唱、说唱、高位爆发兼顾",
        "mask": False,
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")   # 固定引流 CTA（全片最后一句）
for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    show = SHOW_MAP.get(item["key"], SHOW)
    end = q(full_start + show)
    b = {**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start}
    blocks.append(b)
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)       # 升华后消化位 → 固定 CTA
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

intro_dur = intro_end
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_intro.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        "seg_intro.wav",
        "-y",
    ]
)
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            f"{C}/{b['clip']}.mp4",
            "-i",
            f"{A}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
            "-map",
            "[out]",
            "-ac",
            "2",
            "-ar",
            "48000",
            out,
            "-y",
        ]
    )
    segments.append(out)

outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)   # CTA 在 outro 段内的起点
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_qitian.mp4",
        "-i",
        f"{A}/outro.wav",
        "-i",
        f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        "seg_outro.wav",
        "-y",
    ]
)
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
planned_total = total
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, "vert_intro")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_qitian"))

labels = []
masks = []
tweens = []
for idx, b in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    rank_class = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    if b["mask"]:
        masks.append(
            f'<div id="mask{idx}" class="clip lyricMask" data-start="{b["start"]}" '
            f'data-duration="{q(b["end"] - b["start"])}" data-track-index="8"></div>'
        )
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "齐天"), ("02", "斗牛"), ("03", "寒鸦少年"), ("04", "我管你"), ("05", "烟火里的尘埃")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070a;font-family:sans-serif;color:#f8f3ec}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.76),rgba(0,0,0,.12) 32%,rgba(0,0,0,.18) 58%,rgba(0,0,0,.82))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.15) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
.lyricMask{position:absolute;left:0;right:0;top:930px;height:500px;z-index:3;background:rgba(8,7,10,.99);box-shadow:0 -18px 54px rgba(0,0,0,.80),0 18px 54px rgba(0,0,0,.70)}
#cover{position:absolute;inset:0;z-index:5;padding:164px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#e0913f}
.eyebrow:before{content:"";width:52px;height:4px;background:#e0913f;border-radius:99px}
#cover h1{margin-top:28px;font-size:140px;line-height:1.02;font-weight:950;max-width:920px;text-wrap:balance}
#cover .sub{margin-top:28px;font-size:38px;line-height:1.45;color:#d7cfc2;font-weight:650;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:880px}
.chips span{border:1px solid rgba(224,145,63,.55);color:#f4d3ae;background:rgba(10,10,14,.52);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(5,5,8,.82),rgba(5,5,8,.50));border-left:8px solid #e0913f}
.fullLabel .rank{font-size:30px;font-weight:900;color:#e0913f}
.fullLabel h2{margin-top:14px;font-size:84px;line-height:1.06;font-weight:950}
.fullLabel .tag{margin-top:18px;font-size:41px;line-height:1.28;font-weight:850;color:#f3c596}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#cec4b8}
.fullLabel.topRank{border-left-color:#c7333f}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff6a5c}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(5,5,8,.70);border:1px solid rgba(224,145,63,.58);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#e0913f}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(199,51,63,.78)}
.miniLabel.topRank span{color:#ff6a5c}
#outro{position:absolute;z-index:5;inset:0;padding:150px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#e0913f}
#outro h2{margin-top:18px;font-size:72px;line-height:1.13;font-weight:950;max-width:900px}
#outro ol{margin-top:44px;list-style:none;display:grid;gap:16px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(5,5,8,.62);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#e0913f}
#outro li:first-child span{color:#ff6a5c}
#outro li strong{font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.45;color:#d7cfc2;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:96px;text-align:center}
#cta .v{font-size:46px;font-weight:950;color:#ff6a5c;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#e0913f;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += "\n" + "\n".join(masks)
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>华晨宇最难的5首歌</h1>'
    '<p class="sub">不是只比谁唱得高，而是看戏剧感、爆发力、控制力和气息，能不能在同一首歌里同时拉满。</p></div>'
    '<div class="chips"><span>高位爆发</span><span>强声压</span><span>戏剧张力</span><span>摇滚体能</span><span>弱声控制</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>华晨宇的难，是把戏剧、爆发和控制揉进同一口气里。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期按难度从第五到第一收束：烟火里的尘埃、我管你、寒鸦少年、斗牛、齐天。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.from("#cover .eyebrow",{{x:-24,opacity:0,duration:.55,ease:"power2.out"}},0.35);
tl.from("#cover h1",{{y:52,opacity:0,duration:.75,ease:"power4.out"}},0.65);
tl.from("#cover .sub",{{y:28,opacity:0,duration:.55,ease:"power2.out"}},1.15);
tl.from("#cover .chips span",{{y:22,opacity:0,duration:.45,ease:"power2.out",stagger:.08}},1.55);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
tl.from("#cta .v",{{y:26,opacity:0,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.from("#cta .f",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(cta_voice+0.35)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{body}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "huachenyu-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
