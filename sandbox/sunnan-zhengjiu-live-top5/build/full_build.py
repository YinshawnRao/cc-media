#!/usr/bin/env python3
import json
import subprocess
import wave
import contextlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = "audio"
C = "clips"
LEAD = 0.30
DIG = 1.40
BED = 0.16
VOICE_GAIN = 2.0
MASTER_GAIN = 1.25


def dur(wav):
    with contextlib.closing(wave.open(str(ROOT / wav), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


voice_durs = {x["key"]: x["duration"] for x in json.loads((ROOT / "narration.json").read_text())}

INTRO_D = round(LEAD + voice_durs["intro"] + 2.0, 3)

songs = [
    {
        "key": "p5_chinastar",
        "clip": "top5_chinastar",
        "no": "TOP5",
        "title": "《中国之星》版",
        "subtitle": "竞演感最强的一版",
        "tags": ["编曲最豪", "竞演感强", "高音依然炸场"],
        "transition": "年轻时期的孙楠，明显更吓人。",
        "show": 45.0,
    },
    {
        "key": "p4_korea2002",
        "clip": "top4_korea2002",
        "no": "TOP4",
        "title": "2002第四届中韩歌会",
        "subtitle": "最有野性的一版",
        "tags": ["年轻声压", "爆发力强", "野性大于精修感"],
        "transition": "后面还有更稳、更完整的现场。",
        "show": 45.0,
    },
    {
        "key": "p3_changchun2003",
        "clip": "top3_changchun2003",
        "no": "TOP3",
        "title": "2003现场版",
        "subtitle": "声压怪时期的代表",
        "tags": ["开口跪", "副歌声压强", "巅峰机能代表"],
        "transition": "二十多年后，这首歌又被重新唱回来。",
        "show": 45.0,
    },
    {
        "key": "p2_singer2024",
        "clip": "top2_singer2024",
        "no": "TOP2",
        "title": "《歌手2024》直播版",
        "subtitle": "55岁全开麦，仍然能打",
        "tags": ["直播压力拉满", "55岁仍有声压", "口碑翻身现场"],
        "transition": "压力和话题拉满，但第一名还是绕不开那一版。",
        "show": 45.0,
    },
    {
        "key": "p1_korea5",
        "clip": "top1_korea5",
        "no": "TOP1",
        "title": "第五届中韩歌会原Key版",
        "subtitle": "《拯救》Live完成度天花板",
        "tags": ["原Key巅峰", "高音不散", "气息稳定", "完成度最高"],
        "transition": "排名仅代表本期综合判断，欢迎补充其他版本。",
        "show": 35.0,
    },
]


def full_start(key):
    return round(LEAD + voice_durs[key] + 0.2 + DIG, 3)


blocks = []
t = INTRO_D
for song in songs[:4]:
    fs = full_start(song["key"])
    L = round(fs + song["show"], 3)
    blocks.append({**song, "start": t, "L": L, "full": round(t + fs, 3), "end": round(t + L, 3)})
    t = round(t + L, 3)

DUEL_D = 0.0
DUEL_START = t

last = songs[4]
fs = full_start(last["key"])
L = round(fs + last["show"], 3)
blocks.append({**last, "start": t, "L": L, "full": round(t + fs, 3), "end": round(t + L, 3)})
t = round(t + L, 3)

OUTRO_D = round(LEAD + voice_durs["outro"] + 2.0, 3)
OUTRO_START = t
TOTAL = round(t + OUTRO_D, 3)


def env(narr_end, full):
    sw = round(narr_end + 0.2, 3)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{sw}))*{BED}"
        f"+(between(t,{sw},{full}))*({BED}+{1.0-BED}*(t-{sw})/{DIG})"
        f"+(gte(t,{full}))*1.0"
    )


segs = []
run([
    "ffmpeg", "-v", "error", "-i", f"{C}/top2_singer2024.mp4", "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,"
    f"atrim=0:{INTRO_D},volume=0.13,afade=t=in:st=0:d=0.7[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_D},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y"
])
segs.append("seg_intro.wav")

for b in blocks[:4]:
    ne = round(LEAD + voice_durs[b["key"]], 3)
    fs_local = round(b["full"] - b["start"], 3)
    run([
        "ffmpeg", "-v", "error", "-i", f"{C}/{b['clip']}.mp4", "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{b['L']},volume='{env(ne, fs_local)}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['L']},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", f"seg_{b['no']}.wav", "-y"
    ])
    segs.append(f"seg_{b['no']}.wav")

b = blocks[-1]
ne = round(LEAD + voice_durs[b["key"]], 3)
fs_local = round(b["full"] - b["start"], 3)
run([
    "ffmpeg", "-v", "error", "-i", f"{C}/{b['clip']}.mp4", "-i", f"{A}/{b['key']}.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
    f"atrim=0:{b['L']},volume='{env(ne, fs_local)}':eval=frame[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['L']},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", f"seg_{b['no']}.wav", "-y"
])
segs.append(f"seg_{b['no']}.wav")

run([
    "ffmpeg", "-v", "error", "-i", f"{C}/top1_korea5.mp4", "-i", f"{A}/outro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,"
    f"atrim=0:{OUTRO_D},volume=0.16,afade=t=out:st={OUTRO_D-2.0}:d=2.0[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OUTRO_D},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y"
])
segs.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-af", f"volume={MASTER_GAIN},alimiter=limit=0.97", "-ac", "2", "-ar", "48000", "master.wav", "-y"])


def video(id_, src, start, duration, track, cls="main-video", media_start=None):
    ms = f' data-media-start="{media_start}"' if media_start is not None else ""
    return f'<video id="{id_}" class="clip {cls}" data-start="{start}" data-duration="{duration}" data-track-index="{track}" src="{C}/{src}.mp4" muted playsinline{ms}></video>'


videos = []
flash_items = [
    ("top4_korea2002", 18.0, "2002 · 中韩歌会"),
    ("top3_changchun2003", 21.0, "2003 · 现场"),
    ("top2_singer2024", 27.0, "2024 · 直播"),
    ("top1_korea5", 27.0, "原Key · 中韩歌会"),
]
for i, (src, ms, _) in enumerate(flash_items):
    videos.append(video(f"flash{i}", src, round(i * 0.72, 3), 0.86, 20 + i, "flash-video", ms))
videos.append(video("intro_bg", "top2_singer2024", 2.7, round(INTRO_D - 2.7, 3), 0, "main-video", 0))

for i, b in enumerate(blocks[:4]):
    videos.append(video(f"vid_{b['no'].lower()}", b["clip"], b["start"], b["L"], i % 2, "main-video"))
videos.append(video("vid_top1", blocks[-1]["clip"], blocks[-1]["start"], blocks[-1]["L"], 6, "main-video"))
videos.append(video("outro_bg", "top1_korea5", OUTRO_START, OUTRO_D, 7, "main-video", 8))


cards = []
tweens = []
for i, b in enumerate(blocks):
    local_intro_d = round(b["full"] - b["start"], 3)
    card_d = max(local_intro_d - 0.25, 1)
    tags = "".join(f"<span>{x}</span>" for x in b["tags"])
    card = f"""
<section id="card{i}" class="clip rank-card {'rank-one' if b['no']=='TOP1' else ''}" data-start="{round(b['start']+0.1,3)}" data-duration="{card_d}" data-track-index="{40+i}">
  <div class="rank-no">{b['no']}</div>
  <div class="rank-title">{b['title']}</div>
  <div class="rank-sub">{b['subtitle']}</div>
  <div class="rank-tags">{tags}</div>
</section>
<section id="show{i}" class="clip show-label {'rank-one' if b['no']=='TOP1' else ''}" data-start="{b['full']}" data-duration="{round(b['end']-b['full'],3)}" data-track-index="{50+i}">
  <div><b>{b['no']}</b><span>{b['title']}</span></div>
  <p>{b['transition']}</p>
</section>
"""
    cards.append(card)
    s = round(b["start"] + 0.25, 3)
    tweens.append(f'tl.from("#card{i} .rank-no",{{y:60,opacity:0,duration:.55,ease:"power3.out"}},{s});')
    tweens.append(f'tl.from("#card{i} .rank-title",{{y:32,opacity:0,duration:.5,ease:"power3.out"}},{s+0.18});')
    tweens.append(f'tl.from("#card{i} .rank-sub",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{s+0.34});')
    tweens.append(f'tl.from("#card{i} .rank-tags span",{{y:16,opacity:0,duration:.35,ease:"power2.out",stagger:.08}},{s+0.52});')
    tweens.append(f'tl.to("#card{i}",{{opacity:0,y:-18,duration:.35,ease:"power1.in"}},{round(b["full"]-0.45,3)});')
    tweens.append(f'tl.from("#show{i}",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{round(b["full"]+0.08,3)});')

CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#050507;font-family:"PingFang SC","Noto Sans SC",system-ui,sans-serif;color:#fff}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#050507}
.main-video,.flash-video{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
.flash-video{z-index:2;filter:contrast(1.08) saturate(1.15)}
.duel-video{position:absolute;top:0;width:540px;height:1920px;object-fit:cover;z-index:1;filter:contrast(1.03)}
.duel-video.left{left:0}.duel-video.right{right:0}
#global-vignette{position:absolute;inset:0;z-index:8;background:linear-gradient(180deg,rgba(0,0,0,.65) 0%,rgba(0,0,0,.08) 26%,rgba(0,0,0,.18) 56%,rgba(0,0,0,.82) 100%),radial-gradient(90% 68% at 50% 36%,rgba(255,230,170,.10),rgba(0,0,0,0) 55%)}
#grain{position:absolute;inset:0;z-index:80;opacity:.055;mix-blend-mode:soft-light;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch' seed='17'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.stage-frame{position:absolute;left:54px;right:54px;top:456px;height:840px;z-index:9;border:1px solid rgba(232,202,125,.22);box-shadow:0 0 0 999px rgba(0,0,0,.16) inset;pointer-events:none}
.stage-frame:before,.stage-frame:after{content:"";position:absolute;left:0;right:0;height:104px;background:linear-gradient(180deg,rgba(0,0,0,.78),rgba(0,0,0,.22))}
.stage-frame:before{top:0}.stage-frame:after{bottom:0;transform:rotate(180deg)}
.flash-caption{position:absolute;left:70px;right:70px;bottom:250px;z-index:18;font-size:42px;font-weight:800;color:#f7e7bd;letter-spacing:.08em;text-shadow:0 4px 22px rgba(0,0,0,.8)}
#intro-title{position:absolute;inset:0;z-index:22;padding:150px 76px 0;display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:260px}
.eyebrow{display:inline-flex;align-items:center;gap:16px;width:max-content;font-size:30px;font-weight:800;letter-spacing:.22em;color:#e8c87e}
.eyebrow:before{content:"";width:50px;height:4px;border-radius:4px;background:#e8c87e;box-shadow:0 0 24px rgba(232,200,126,.7)}
#intro-title h1{font-size:94px;line-height:1.04;margin-top:22px;font-weight:900;letter-spacing:0;color:#fff;text-shadow:0 8px 42px rgba(0,0,0,.6)}
#intro-title h1 b{font-size:118px;background:linear-gradient(104deg,#fff6d8,#e8c87e 56%,#fff);-webkit-background-clip:text;background-clip:text;color:transparent}
#intro-title .rule{margin-top:26px;font-size:40px;font-weight:800;color:#f0f0f0}
#intro-title .criteria{display:flex;flex-wrap:wrap;gap:14px;margin-top:34px}
#intro-title .criteria span{font-size:30px;font-weight:800;padding:10px 18px;border:1px solid rgba(232,200,126,.45);background:rgba(7,7,10,.58);color:#f4dfad}
.rank-card{position:absolute;left:72px;right:72px;bottom:210px;z-index:24;padding:42px 44px 46px;border-left:8px solid #e8c87e;background:linear-gradient(180deg,rgba(7,7,10,.84),rgba(7,7,10,.70));box-shadow:0 24px 80px rgba(0,0,0,.55)}
.rank-card.rank-one{border-left-color:#fff3c7;background:linear-gradient(180deg,rgba(14,11,6,.88),rgba(7,7,10,.70))}
.rank-no{font-family:"Arial Black",Impact,sans-serif;font-size:92px;line-height:.88;color:#e8c87e;letter-spacing:0}
.rank-one .rank-no{font-size:108px;background:linear-gradient(104deg,#fff7d4,#e8c87e 50%,#fff);-webkit-background-clip:text;background-clip:text;color:transparent}
.rank-title{font-size:58px;font-weight:900;line-height:1.12;margin-top:18px}
.rank-sub{font-size:34px;font-weight:800;color:#f2dfad;margin-top:14px}
.rank-tags{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}
.rank-tags span{font-size:27px;font-weight:800;color:#fff;padding:9px 16px;border-radius:999px;background:rgba(232,200,126,.18);border:1px solid rgba(232,200,126,.36)}
.show-label{position:absolute;left:62px;right:62px;bottom:126px;z-index:28;padding:24px 30px 26px;background:linear-gradient(180deg,rgba(0,0,0,.86),rgba(0,0,0,.68));border:1px solid rgba(232,200,126,.24);box-shadow:0 18px 64px rgba(0,0,0,.55)}
.show-label div{display:flex;align-items:baseline;gap:18px}.show-label b{font-size:54px;color:#e8c87e}.show-label span{font-size:38px;font-weight:900}.show-label p{margin-top:8px;font-size:25px;color:#ddd;line-height:1.34}
.duel-card{position:absolute;inset:0;z-index:30;display:flex;align-items:flex-end;padding:0 54px 190px;gap:36px}
.duel-card .side{flex:1;background:rgba(0,0,0,.72);border:1px solid rgba(232,200,126,.28);padding:26px 24px;min-height:210px}
.duel-card .side h3{font-size:34px;color:#e8c87e}.duel-card .side p{font-size:38px;font-weight:900;line-height:1.18;margin-top:12px}.duel-card .split{position:absolute;left:535px;top:410px;bottom:410px;width:10px;background:linear-gradient(180deg,rgba(232,200,126,0),#e8c87e,rgba(232,200,126,0));box-shadow:0 0 38px rgba(232,200,126,.9)}
#outro{position:absolute;left:70px;right:70px;top:300px;z-index:30;padding:46px 42px;background:linear-gradient(180deg,rgba(0,0,0,.82),rgba(0,0,0,.64));border:1px solid rgba(232,200,126,.24)}
#outro h2{font-size:70px;line-height:1.08;background:linear-gradient(104deg,#fff6d8,#e8c87e 54%,#fff);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro p{font-size:40px;line-height:1.35;font-weight:800;margin-top:28px}
#outro .fine{font-size:24px;color:#cfc6ad;margin-top:34px;line-height:1.42}
"""

intro_flash_labels = "\n".join(
    f'<div id="fc{i}" class="clip flash-caption" data-start="{round(i*.72,3)}" data-duration=".72" data-track-index="{70+i}">{label}</div>'
    for i, (_, _, label) in enumerate(flash_items)
)

html = f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1080,height=1920">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{''.join(videos)}
<div id="global-vignette" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="10"></div>
<div id="grain" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="11"></div>
<div id="stage-frame" class="clip stage-frame" data-start="0" data-duration="{TOTAL}" data-track-index="12"></div>
{intro_flash_labels}
<section id="intro-title" class="clip" data-start="3.05" data-duration="{round(INTRO_D-3.05,3)}" data-track-index="25">
  <div class="eyebrow">只看现场</div>
  <h1>《拯救》Live<br><b>完成度TOP5</b></h1>
  <div class="rule">不看情怀滤镜，不做绝对权威</div>
  <div class="criteria"><span>音准</span><span>气息</span><span>高音质量</span><span>现场压力</span><span>情绪推进</span></div>
</section>
{''.join(cards)}
<section id="outro" class="clip" data-start="{OUTRO_START+0.2}" data-duration="{OUTRO_D-0.2}" data-track-index="66">
  <h2>你心中的《拯救》最强Live是哪一版？</h2>
  <p>《歌手2024》能反超中韩歌会吗？</p>
  <p class="fine">本期排名按演唱完成度、现场状态与社区讨论综合判断，欢迎补充其他版本。</p>
</section>
<audio id="master" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="90" src="master.wav"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.from("#intro-title .eyebrow", {{x:-24, opacity:0, duration:.45, ease:"power2.out"}}, 3.15);
tl.from("#intro-title h1", {{y:46, opacity:0, duration:.65, ease:"power3.out"}}, 3.35);
tl.from("#intro-title .rule", {{y:20, opacity:0, duration:.45, ease:"power2.out"}}, 4.05);
tl.from("#intro-title .criteria span", {{y:14, opacity:0, duration:.32, stagger:.06, ease:"power2.out"}}, 4.45);
tl.to("#intro-title", {{opacity:0, y:-20, duration:.4, ease:"power1.in"}}, {INTRO_D-0.45});
tl.set("#intro-title", {{opacity:0}}, {INTRO_D});
{chr(10).join(tweens)}
tl.from("#outro h2", {{y:42, opacity:0, duration:.65, ease:"power3.out"}}, {OUTRO_START+0.45});
tl.from("#outro p", {{y:22, opacity:0, duration:.45, stagger:.16, ease:"power2.out"}}, {OUTRO_START+1.0});
window.__timelines["main"] = tl;
</script>
</body>
</html>"""

(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "meta.json").write_text('{"id":"main","name":"sunnan-zhengjiu-live-top5"}', encoding="utf-8")
(ROOT / "hyperframes.json").write_text('{"compositions":["index.html"]}', encoding="utf-8")
(ROOT / "package.json").write_text(json.dumps({
    "name": "sunnan-zhengjiu-live-top5",
    "private": True,
    "type": "module",
    "scripts": {
        "check": "npx --yes hyperframes@0.6.69 lint && npx --yes hyperframes@0.6.69 inspect",
        "render": "npx --yes hyperframes@0.6.69 render --sdr",
    },
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL", TOTAL, "INTRO", INTRO_D, "DUEL", DUEL_START, DUEL_D, "OUTRO", OUTRO_START)
