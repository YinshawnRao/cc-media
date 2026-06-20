#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 胡彦斌最难的5首歌."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 38.0
SHOW_MAP = {
    "p5_shiye": 32.0,
    "p4_juebieshi": 34.0,
    "p3_hongyan": 26.0,
}
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
MGAIN = {
    "p5_shiye": 1.05,
    "p4_juebieshi": 1.12,
    "p3_hongyan": 1.00,
    "p2_yueguang": 1.00,
    "p1_quannazou": 1.00,
}


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
        "key": "p5_shiye",
        "clip": "vert_shiye",
        "no": "05",
        "name": "《失业情歌》",
        "plain": "失业情歌",
        "tag": "叙事节奏比高音更刁钻",
        "note": "念白式咬字、生活感、副歌情绪",
    },
    {
        "key": "p4_juebieshi",
        "clip": "vert_juebieshi",
        "no": "04",
        "name": "《诀别诗》",
        "plain": "诀别诗",
        "tag": "悲壮要撑开，不能硬喊",
        "note": "影视主题曲张力、长线条、气息",
    },
    {
        "key": "p3_hongyan",
        "clip": "vert_hongyan",
        "no": "03",
        "name": "《红颜》",
        "plain": "红颜",
        "tag": "流行唱法里要有江湖感",
        "note": "中国风腔体、柔韧线条、侠气",
    },
    {
        "key": "p2_yueguang",
        "clip": "vert_yueguang",
        "no": "02",
        "name": "《月光》",
        "plain": "月光",
        "tag": "国风腔体和 R&B 转音叠加",
        "note": "假声控制、发声位置、咬字稳定",
    },
    {
        "key": "p1_quannazou",
        "clip": "vert_quannazou",
        "no": "01",
        "name": "《你要的全拿走》",
        "plain": "你要的全拿走",
        "tag": "密、长、急、绕，全都叠满",
        "note": "高速咬字、讽刺情绪、气息控制",
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")
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
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start, "show": show})
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    ramp = max(0.45, q(full_start_local - swell))
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{ramp})"
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
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95:level=false[out]",
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
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={MGAIN.get(b['key'], 1.0)}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.92:level=false[out]",
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
cta_local = q(cta_voice - outro_start)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_quannazou.mp4",
        "-i",
        f"{A}/outro.wav",
        "-i",
        f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95:level=false[out]",
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
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_quannazou"))

labels = []
tweens = []
for idx, b in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    rank_class = " topRank" if b["no"] == "01" else ""
    full_track = 2 if idx % 2 == 0 else 8
    mini_track = 4 if idx % 2 == 0 else 9
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="{full_track}">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="{mini_track}">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:30,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:48,opacity:0}},{{y:0,opacity:1,duration:.62,ease:"power4.out"}},{q(b["start"]+.34)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"expo.out"}},{q(b["start"]+.74)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.42,ease:"sine.out"}},{q(b["start"]+.98)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.42)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-26,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power3.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "失业情歌"),
        ("04", "诀别诗"),
        ("03", "红颜"),
        ("02", "月光"),
        ("01", "你要的全拿走"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070a;font-family:sans-serif;color:#f8f3ee}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,7,10,.76),rgba(8,7,10,.16) 30%,rgba(8,7,10,.24) 58%,rgba(8,7,10,.86))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.11;background:repeating-linear-gradient(0deg,rgba(255,255,255,.16) 0 1px,transparent 1px 5px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:158px 72px 148px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#d99a45}
.eyebrow:before{content:"";width:56px;height:5px;background:#d84b3f;border-radius:99px}
#cover h1{margin-top:34px;font-size:132px;line-height:1.02;font-weight:950;max-width:920px;text-shadow:0 18px 54px rgba(0,0,0,.55)}
#cover h1 span{display:block;color:#d84b3f}
#cover .sub{margin-top:30px;font-size:39px;line-height:1.42;color:#d1c8bd;font-weight:680;max-width:880px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:2px solid rgba(217,154,69,.62);color:#f1c68e;background:rgba(8,7,10,.55);font-size:28px;font-weight:820;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:68px;right:68px;bottom:194px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(8,7,10,.84),rgba(8,7,10,.52));border-left:8px solid #d99a45;box-shadow:0 24px 80px rgba(0,0,0,.38)}
.fullLabel .rank{font-size:30px;font-weight:950;color:#d99a45}
.fullLabel h2{margin-top:14px;font-size:78px;line-height:1.08;font-weight:950;max-width:900px}
.fullLabel .tag{margin-top:18px;font-size:39px;line-height:1.28;font-weight:880;color:#f0bd7f}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:680;color:#d1c8bd}
.fullLabel.topRank{border-left-color:#d84b3f}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff6b5c}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(8,7,10,.72);border:2px solid rgba(217,154,69,.58);border-radius:8px;backdrop-filter:blur(8px)}
.miniLabel span{font-size:44px;font-weight:950;color:#d99a45}
.miniLabel strong{font-size:38px;font-weight:920}
.miniLabel.topRank{border-color:rgba(216,75,63,.78)}
.miniLabel.topRank span{color:#ff6b5c}
#outro{position:absolute;z-index:5;inset:0;padding:146px 74px 170px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:900;color:#d99a45}
#outro h2{margin-top:18px;font-size:70px;line-height:1.16;font-weight:950;max-width:910px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:16px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:22px;padding:18px 22px;background:rgba(8,7,10,.66);border:2px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#d99a45;font-variant-numeric:tabular-nums}
#outro li:last-child span{color:#ff6b5c}
#outro li strong{font-size:33px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.45;color:#d1c8bd;font-weight:680}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:22px 28px;background:rgba(8,7,10,.62);border:2px solid rgba(216,75,63,.55);border-radius:8px}
#cta .v{font-size:43px;font-weight:950;color:#ff6b5c;line-height:1.2}
#cta .f{margin-top:14px;font-size:34px;font-weight:880;color:#d99a45}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>胡彦斌<span>最难的5首歌</span></h1>'
    '<p class="sub">不只看高音，也看节奏、咬字、转音、气息和表达，能不能在同一首歌里同时稳住。</p></div>'
    '<div class="chips"><span>高速咬字</span><span>假声转音</span><span>中国风腔体</span><span>影视悲壮感</span><span>叙事节奏</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>胡彦斌的难，是把技术藏进表达里。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这份排名从第五名一路推到第一名，越往前越考验气息、节奏和完整表达。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.fromTo("#cover .eyebrow",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.52,ease:"power2.out"}},0.35);
tl.fromTo("#cover h1",{{y:56,opacity:0}},{{y:0,opacity:1,duration:.78,ease:"power4.out"}},0.64);
tl.fromTo("#cover .sub",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.56,ease:"expo.out"}},1.12);
tl.fromTo("#cover .chips span",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.46,ease:"sine.out",stagger:.08}},1.52);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.66,ease:"power4.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-32,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"expo.out",stagger:.1}},{q(outro_start+1.15)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.46,ease:"sine.out"}},{q(outro_start+2.0)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power3.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"expo.out"}},{q(cta_voice+0.35)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "huyanbin-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
(ROOT / "timeline.json").write_text(
    json.dumps(
        {
            "total": total,
            "intro_end": intro_end,
            "blocks": blocks,
            "outro_start": outro_start,
            "cta_voice": cta_voice,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
