#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 梁静茹最苦的5首歌 (saddest top 5)."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {  # trim studio MVs / lift the dynamic live tracks toward a uniform ~-15dB RMS
    "huiguoqu": 0.90, "chongbai": 1.05, "manleng": 0.92, "kexi": 1.30, "huxi": 1.10,
}
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6

INTRO_CLIP = "vert_cover"
OUTRO_CLIP = "vert_huxi"


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
        "key": "huiguoqu", "clip": "vert_huiguoqu", "no": "05",
        "name": "《会过去的》", "plain": "会过去的", "year": "2009", "show": 34.0,
        "tag": "越平静，越疼",
        "note": "表面是疗愈，其实是还没真正好起来。",
    },
    {
        "key": "chongbai", "clip": "vert_chongbai", "no": "04",
        "name": "《崇拜》", "plain": "崇拜", "year": "2007", "show": 34.0,
        "tag": "卑微的仰望",
        "note": "把对方放太高，清醒后才看见那份不对等。",
    },
    {
        "key": "manleng", "clip": "vert_manleng", "no": "03",
        "name": "《慢冷》", "plain": "慢冷", "year": "2010", "show": 34.0,
        "tag": "后劲型的苦",
        "note": "当下没崩溃，越往后越疼，慢慢困在回忆里。",
    },
    {
        "key": "kexi", "clip": "vert_kexi", "no": "02",
        "name": "《可惜不是你》", "plain": "可惜不是你", "year": "2006", "show": 34.0,
        "tag": "遗憾系天花板",
        "note": "差一点圆满，差一点，就是永远。",
    },
    {
        "key": "huxi", "clip": "vert_huxi", "no": "01",
        "name": "《会呼吸的痛》", "plain": "会呼吸的痛", "year": "2007", "show": 40.0,
        "tag": "想念是会呼吸的痛",
        "note": "分开以后，一个人替两个人，把日子继续过完。",
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + item["show"])
    b = {**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start}
    blocks.append(b)
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
total = q(outro_voice_end + OUTRO_TAIL)


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
run([
    "ffmpeg", "-v", "error",
    "-i", f"{C}/{INTRO_CLIP}.mp4",
    "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    run([
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{b['clip']}.mp4",
        "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

outro_dur = q(total - outro_start)
run([
    "ffmpeg", "-v", "error",
    "-i", f"{C}/{OUTRO_CLIP}.mp4",
    "-i", f"{A}/outro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.4}:d=1.4[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
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


videos = [video_tag(0, 0, intro_end, INTRO_CLIP)]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), OUTRO_CLIP))

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
        f'<div class="rk"><span class="rkno">第 {b["no"]} 名</span><span class="rkyr">{b["year"]}</span></div>'
        f'<h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.append(f'tl.from("#{fid} .rk",{{y:26,opacity:0,duration:.5,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:46,opacity:0,duration:.7,ease:"power3.out"}},{q(b["start"]+.36)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(b["start"]+.74)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(b["start"]+.98)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{q(b["full_start"]-.45)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.5,ease:"power2.out"}},{q(b["full_start"]+.12)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["end"]-.4)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{q(b["end"])});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "会呼吸的痛"), ("02", "可惜不是你"), ("03", "慢冷"), ("04", "崇拜"), ("05", "会过去的")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070c;color:#f6f0f1;
  font-family:'Noto Sans SC',sans-serif;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070c}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,6,12,.82),rgba(8,6,12,.10) 30%,rgba(8,6,12,.16) 56%,rgba(8,6,12,.86))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 42%,transparent 52%,rgba(6,4,10,.55) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.10;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
/* cover */
#cover{position:absolute;inset:0;z-index:5;padding:150px 76px 142px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;letter-spacing:.14em;color:#e89aa6}
.eyebrow:before{content:"";width:54px;height:3px;background:#e89aa6;border-radius:99px}
#cover h1{font-family:'Noto Serif SC',serif;font-weight:900;font-size:138px;line-height:1.03;letter-spacing:.02em;
  text-shadow:0 6px 40px rgba(0,0,0,.6);max-width:920px}
#cover h1 em{font-style:normal;color:#f1a9b4}
#cover .sub{margin-top:30px;font-size:37px;line-height:1.5;color:#ddd0d4;font-weight:500;max-width:840px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(232,154,166,.5);color:#f4cdd4;background:rgba(12,9,16,.5);
  font-size:28px;font-weight:600;padding:12px 20px;border-radius:999px}
/* per-song full label */
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:178px;padding:34px 38px 40px;
  background:linear-gradient(135deg,rgba(7,5,11,.84),rgba(7,5,11,.46));backdrop-filter:blur(3px);
  border-left:7px solid #e89aa6;border-radius:6px}
.fullLabel .rk{display:flex;align-items:baseline;gap:18px}
.fullLabel .rkno{font-size:31px;font-weight:900;letter-spacing:.06em;color:#e89aa6}
.fullLabel .rkyr{font-size:25px;font-weight:700;color:#9a8f94;letter-spacing:.1em}
.fullLabel h2{font-family:'Noto Serif SC',serif;margin-top:14px;font-size:92px;line-height:1.04;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:44px;line-height:1.25;font-weight:800;color:#f3b6bf}
.fullLabel .note{margin-top:14px;font-size:32px;line-height:1.4;font-weight:500;color:#cfc4c8}
.fullLabel.topRank{border-left-color:#ff5566}
.fullLabel.topRank .rkno,.fullLabel.topRank .tag{color:#ff7882}
/* showcase mini tag */
.miniLabel{position:absolute;z-index:5;top:92px;left:54px;display:flex;align-items:center;gap:16px;
  padding:12px 20px;background:rgba(7,5,11,.62);border:1px solid rgba(232,154,166,.5);border-radius:999px}
.miniLabel span{font-size:42px;font-weight:900;color:#e89aa6}
.miniLabel strong{font-family:'Noto Serif SC',serif;font-size:38px;font-weight:800}
.miniLabel.topRank{border-color:rgba(255,85,102,.66)}
.miniLabel.topRank span{color:#ff7882}
/* outro */
#outro{position:absolute;z-index:5;inset:0;padding:128px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:800;letter-spacing:.14em;color:#e89aa6}
#outro h2{font-family:'Noto Serif SC',serif;margin-top:20px;font-size:70px;line-height:1.16;font-weight:800;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:19px 26px;
  background:rgba(7,5,11,.58);border:1px solid rgba(255,255,255,.1);border-radius:8px}
#outro li span{font-size:34px;font-weight:900;color:#e89aa6}
#outro li:first-child{border-color:rgba(255,85,102,.5);background:rgba(40,8,14,.5)}
#outro li:first-child span{color:#ff7882}
#outro li strong{font-family:'Noto Serif SC',serif;font-size:40px;font-weight:800}
#outro .close{margin-top:34px;font-size:33px;line-height:1.5;color:#ddd0d4;font-weight:500;max-width:900px}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="5"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.3)}" data-track-index="2">'
    '<div><div class="eyebrow">情歌里最苦的那一面</div>'
    '<h1>梁静茹<br>最苦的<em>5</em>首歌</h1>'
    '<p class="sub">不是热恋，是错过、是想念、是清醒之后才发现的不对等——她把心碎，唱得很轻，也很疼。</p></div>'
    '<div class="chips"><span>越平静越疼</span><span>遗憾系天花板</span><span>后劲型的苦</span><span>会呼吸的想念</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最 苦 榜 单</div><h2>她最苦的，不是撕心裂肺，<br>是平静底下，没真正过去的那一种。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">第五《会过去的》、第四《崇拜》、第三《慢冷》、第二《可惜不是你》、第一《会呼吸的痛》。</p></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1}},0);
tl.from("#cover .eyebrow",{{x:-22,duration:.7,ease:"power2.out"}},0.12);
tl.from("#cover h1",{{y:30,duration:.95,ease:"power3.out"}},0.2);
tl.from("#cover .sub",{{y:20,duration:.7,ease:"power2.out"}},0.5);
tl.from("#cover .chips span",{{y:16,duration:.55,ease:"power2.out",stagger:.08}},0.7);
tl.to("#cover h1",{{scale:1.02,transformOrigin:"left center",duration:4.5,yoyo:true,repeat:1,ease:"sine.inOut"}},4);
tl.to("#cover",{{opacity:0,duration:.45,ease:"power1.in"}},{q(intro_end-.6)});
tl.set("#cover",{{opacity:0}},{q(intro_end-.1)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:20,opacity:0,duration:.55,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:38,opacity:0,duration:.7,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-30,opacity:0,duration:.5,ease:"power2.out",stagger:.12}},{q(outro_start+1.25)});
tl.from("#outro .close",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+2.2)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Serif+SC:wght@600;700;900&display=swap" rel="stylesheet">
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "liangjingru-saddest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
