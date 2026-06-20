#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Yisa Yu hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 38.0
LEAD = 0.35
DIG = 1.55
BED = 0.14
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 0.8
DIGEST_O = 1.0
OUTRO_TAIL = 2.6
MGAIN = {
    "p5_shijianzhuyu": 1.08,
    "p2_zhiwang": 1.08,
    "p1_luguorenjian": 1.12,
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
        "key": "p5_shijianzhuyu",
        "clip": "vert_shijianzhuyu",
        "no": "05",
        "name": "《时间煮雨》",
        "plain": "时间煮雨",
        "tag": "看似简单，最怕唱平",
        "note": "气息要干净，青春回望不能哭满",
    },
    {
        "key": "p4_simu",
        "clip": "vert_simu",
        "no": "04",
        "name": "《思慕》",
        "plain": "思慕",
        "tag": "古风长线条里的宿命感",
        "note": "气口、咬字、铺陈都不能太现代",
    },
    {
        "key": "p3_zhifou",
        "clip": "vert_zhifou",
        "no": "03",
        "name": "《知否知否》",
        "plain": "知否知否",
        "tag": "留白和合唱分寸最难",
        "note": "有词牌感，还要托住对方声线",
    },
    {
        "key": "p2_zhiwang",
        "clip": "vert_zhiwang",
        "no": "02",
        "name": "《指望》",
        "plain": "指望",
        "tag": "高位长句，委屈感不能硬",
        "note": "支撑要够，声音还要保持柔软",
    },
    {
        "key": "p1_luguorenjian",
        "clip": "vert_luguorenjian",
        "no": "01",
        "name": "《路过人间》",
        "plain": "路过人间",
        "tag": "不是炸，是克制到极致",
        "note": "轻、撑、疲惫和温柔都要同时在场",
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
    end = q(full_start + SHOW)
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start})
    t = q(end)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_start = q(outro_voice_end + DIGEST_O)
cta_end = q(cta_start + d_cta)
total_planned = q(cta_end + OUTRO_TAIL)


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
        f"{C}/vert_shijianzhuyu.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.16,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
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

outro_dur = q(total_planned - outro_start)
cta_local = q(cta_start - outro_start)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_luguorenjian.mp4",
        "-i",
        f"{A}/outro.wav",
        "-i",
        f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.18,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
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
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", total_planned)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, "vert_cover_simu")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_luguorenjian"))

labels = []
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
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.48,ease:"expo.out"}},{q(b["start"]+.74)});')
    tweens.append(f'tl.from("#{fid} .note",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.98)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "路过人间"), ("02", "指望"), ("03", "知否知否"), ("04", "思慕"), ("05", "时间煮雨")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080b;font-family:"PingFang SC","Hiragino Sans GB",system-ui,sans-serif;color:#f4efe8}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07080b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(7,8,11,.78),rgba(7,8,11,.2) 32%,rgba(7,8,11,.24) 58%,rgba(7,8,11,.82))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:156px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#d8b06a}
.eyebrow:before{content:"";width:52px;height:4px;background:#d8b06a;border-radius:99px}
#cover h1{margin-top:26px;font-family:"Songti SC","STSong",serif;font-size:126px;line-height:1.04;font-weight:900;max-width:920px}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.45;color:#d7cec1;font-weight:650;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:860px}
.chips span{border:1px solid rgba(216,176,106,.56);color:#f0d49d;background:rgba(15,17,23,.56);font-size:28px;font-weight:750;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(15,17,23,.84),rgba(15,17,23,.5));border-left:8px solid #d8b06a}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:900;color:#d8b06a}
.fullLabel h2{margin-top:14px;font-family:"Songti SC","STSong",serif;font-size:86px;line-height:1.06;font-weight:900}
.fullLabel .tag{margin-top:18px;font-size:42px;line-height:1.28;font-weight:850;color:#f0d49d}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#d7cec1}
.fullLabel.topRank{border-left-color:#b84a62}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ef8191}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;max-width:910px;padding:12px 18px;background:rgba(15,17,23,.7);border:1px solid rgba(216,176,106,.58);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:950;color:#d8b06a}
.miniLabel strong{font-size:38px;font-weight:900;white-space:nowrap}
.miniLabel.topRank{border-color:rgba(184,74,98,.78)}
.miniLabel.topRank span{color:#ef8191}
#outro{position:absolute;z-index:5;inset:0;padding:148px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#d8b06a}
#outro h2{margin-top:18px;font-family:"Songti SC","STSong",serif;font-size:72px;line-height:1.15;font-weight:900;max-width:910px}
#outro ol{margin-top:44px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:18px 22px;background:rgba(15,17,23,.64);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:34px;font-weight:950;color:#d8b06a}
#outro li:first-child span{color:#ef8191}
#outro li strong{font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.45;color:#d7cec1;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:156px;padding:26px 28px;background:rgba(15,17,23,.72);border:1px solid rgba(216,176,106,.5);border-left:8px solid #d8b06a;border-radius:8px;color:#f4efe8}
#cta .vote{font-size:44px;line-height:1.24;font-weight:900;color:#f0d49d}
#cta .follow{margin-top:14px;font-size:34px;line-height:1.34;font-weight:850;color:#f4efe8}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>郁可唯<br>最难的5首歌</h1>'
    '<p class="sub">不只比高音，而是比气息、咬字、分寸和人生感，能不能在同一口气里稳住。</p></div>'
    '<div class="chips"><span>克制表达</span><span>古风留白</span><span>长句支撑</span><span>影视情绪</span><span>副歌控制</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>郁可唯的难，是轻轻唱，却让情绪自己落下来。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期的第一，不给最炫的高音，而给最难拿捏的克制表达。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{cta_start}" data-duration="{q(total-cta_start)}" data-track-index="4">'
    '<div class="vote">你最想为哪一首投票？评论区告诉我。</div>'
    '<div class="follow">记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.from("#cover .eyebrow",{{x:-24,opacity:0,duration:.55,ease:"power2.out"}},0.35);
tl.from("#cover h1",{{y:52,opacity:0,duration:.75,ease:"power4.out"}},0.65);
tl.from("#cover .sub",{{y:28,opacity:0,duration:.55,ease:"power2.out"}},1.15);
tl.from("#cover .chips span",{{y:22,opacity:0,duration:.45,ease:"expo.out",stagger:.08}},1.55);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"expo.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
tl.from("#cta",{{y:30,opacity:0,duration:.5,ease:"power3.out"}},{q(cta_start+.1)});
tl.to("#cta",{{opacity:0,duration:.65,ease:"power1.in"}},{q(total-.9)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "yukewei-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "s")
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
print("outro:", outro_start, "cta:", cta_start, "total:", total)
