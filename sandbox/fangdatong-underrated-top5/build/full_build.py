#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 方大同最被低估的5首歌 (countdown 5->1).

Adapted from the proven sandbox/xujiaying-hardest-top5 template:
- female narration (audio/*.wav from narrate_segments.py)
- per-song self-contained audio segment: bed -> swell -> full showcase, loudnorm=I=-14
- footage = clips/vert_<song>.mp4 (already letterboxed + watermark/lyric clean, 58s each)
- cover = no ranking; outro reveals ranking list.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 34.0          # continuous showcase per song (clip is 58s so block <= clip)
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {"p3_heidongli": 1.1}   # tuned via volumedetect: over clipped w/ boost (removed); heidongli was -16.5
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.5

INTRO_CLIP = "vert_cover"   # warm 方大同 closeup, no ranking reveal
OUTRO_CLIP = "vert_takeme"


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

items = [
    {"key": "p5_over", "clip": "vert_over", "no": "05", "name": "《Over》", "plain": "Over",
     "tag": "歌迷越听越懂的隐藏款", "note": "灵魂乐的律动，松弛、细腻、耐听"},
    {"key": "p4_nuan", "clip": "vert_nuan", "no": "04", "name": "《暖》", "plain": "暖",
     "tag": "非典型情歌里的一束光", "note": "写的不只是爱情，还有关怀与温度"},
    {"key": "p3_heidongli", "clip": "vert_heidongli", "no": "03", "name": "《黑洞里》", "plain": "黑洞里",
     "tag": "被忽略的高级情歌", "note": "把灵魂乐的和声自然放进华语歌"},
    {"key": "p2_orangemoon", "clip": "vert_orangemoon", "no": "02", "name": "《Orange Moon》", "plain": "Orange Moon",
     "tag": "彩蛋级的遗珠", "note": "一人一把吉他，《倒带人生》最早的雏形"},
    {"key": "p1_takeme", "clip": "vert_takeme", "no": "01", "name": "《Take Me》", "plain": "Take Me",
     "tag": "被主打盖住的那股爽感", "note": "不靠苦情，用律动把人带起来"},
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
    end = q(full_start + SHOW)
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
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{INTRO_CLIP}.mp4",
        "-i", f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
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
            "ffmpeg", "-v", "error",
            "-i", f"{C}/{b['clip']}.mp4",
            "-i", f"{A}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(total - outro_start)
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{OUTRO_CLIP}.mp4",
        "-i", f"{A}/outro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.2}:d=1.2[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
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
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["name"]}</strong></section>'
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
    for n, name in [("01", "《Take Me》"), ("02", "《Orange Moon》"), ("03", "《黑洞里》"), ("04", "《暖》"), ("05", "《Over》")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0805;font-family:"Noto Sans SC",sans-serif;color:#f7f1e8}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a0805}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,6,4,.80),rgba(8,6,4,.10) 32%,rgba(8,6,4,.16) 56%,rgba(8,6,4,.82))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.10;background:repeating-linear-gradient(0deg,rgba(255,236,200,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:150px 76px 140px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;color:#e9b35a;letter-spacing:.06em}
.eyebrow:before{content:"";width:54px;height:4px;background:#e9b35a;border-radius:99px}
#cover h1{font-family:"Noto Serif SC",serif;font-size:130px;line-height:1.05;font-weight:900;max-width:920px;text-wrap:balance;text-shadow:0 6px 40px rgba(0,0,0,.6)}
#cover .sub{margin-top:32px;font-size:39px;line-height:1.5;color:#ddd2c2;font-weight:500;max-width:880px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(233,179,90,.5);color:#f3dcab;background:rgba(10,8,5,.46);font-size:29px;font-weight:600;padding:12px 20px;border-radius:9px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:200px;padding:36px 36px 40px;background:linear-gradient(135deg,rgba(10,8,5,.82),rgba(10,8,5,.40));border-left:8px solid #e9b35a;border-radius:4px;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:31px;font-weight:800;color:#e9b35a;letter-spacing:.14em}
.fullLabel h2{font-family:"Noto Serif SC",serif;margin-top:14px;font-size:90px;line-height:1.05;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:43px;line-height:1.28;font-weight:700;color:#f4d59c}
.fullLabel .note{margin-top:12px;font-size:32px;line-height:1.4;font-weight:400;color:#d2c6b6}
.fullLabel.topRank{border-left-color:#ff9a3c}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ffb05a}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 22px;background:rgba(10,8,5,.62);border:1px solid rgba(233,179,90,.55);border-radius:9px}
.miniLabel span{font-size:44px;font-weight:900;color:#e9b35a}
.miniLabel strong{font-family:"Noto Serif SC",serif;font-size:40px;font-weight:800}
.miniLabel.topRank{border-color:rgba(255,154,60,.75)}
.miniLabel.topRank span{color:#ffb05a}
#outro{position:absolute;z-index:5;inset:0;padding:140px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:33px;font-weight:800;color:#e9b35a;letter-spacing:.14em}
#outro h2{font-family:"Noto Serif SC",serif;margin-top:20px;font-size:72px;line-height:1.16;font-weight:900;max-width:920px}
#outro ol{margin-top:46px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;gap:26px;padding:18px 24px;background:rgba(10,8,5,.56);border:1px solid rgba(255,236,200,.12);border-radius:10px}
#outro li span{font-size:35px;font-weight:900;color:#e9b35a;min-width:58px}
#outro li:first-child{background:rgba(255,154,60,.12);border-color:rgba(255,154,60,.34)}
#outro li:first-child span{color:#ffb05a}
#outro li strong{font-family:"Noto Serif SC",serif;font-size:42px;font-weight:800}
#outro .close{margin-top:36px;font-size:33px;line-height:1.5;color:#ddd2c2;font-weight:500}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 唱作盘点</div><h1>方大同最被低估的5首歌</h1>'
    '<p class="sub">传唱度最高的那几首之外，这五首遗珠，把他最高级的功夫，藏在最不张扬的地方。</p></div>'
    '<div class="chips"><span>灵魂乐</span><span>节奏蓝调</span><span>唱作全才</span><span>内行才懂</span><span>专辑遗珠</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">完整榜单</div><h2>方大同的厉害，是把功夫藏进最不张扬的歌里。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：Over、暖、黑洞里、Orange Moon、Take Me。</p></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
/* Cover must be COMPLETE at frame 0 (it is the thumbnail) -> no opacity fade-in.
   Elements are visible from t=0; motion comes from the live footage + a subtle h1 breath. */
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.02,duration:3.0,ease:"sine.inOut",yoyo:true,repeat:1}},0.3);
tl.to("#cover",{{opacity:0,duration:.4,ease:"power1.in"}},{q(intro_end-.55)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Serif+SC:wght@500;700;900&display=swap" rel="stylesheet">
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "fangdatong-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
