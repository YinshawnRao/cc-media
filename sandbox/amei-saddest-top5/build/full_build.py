#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 张惠妹最苦的5首歌 (countdown 5->1).

Each clips/vert_<key>.mp4 carries its own source audio ([0:a]=music); narration ducks it.
倒数揭晓：连名带姓⑤ → 掉了④ → 剪爱③ → 我恨我爱你② → 人质① (压轴).
片尾：作品 outro 升华 → 消化位 → 固定引流 CTA（全片最后一句）。
"""
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
MGAIN = {}  # lmdx 改用官方 MV 录音室原声后重新校准
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
CTA_GAP = 1.0      # 消化位：作品 outro 念完到固定 CTA 之间
OUTRO_TAIL = 1.8   # CTA 念完留尾再 fade
INTRO_CLIP = "vert_cover"     # cover bg = 人质 4K 黑白正脸 (首帧 02:40)
OUTRO_CLIP = "vert_renzhi"    # 压轴 B&W 衬底榜单揭晓


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

# countdown reveal order 5 -> 1
items = [
    {
        "key": "lianmingdaixing", "clip": "vert_lianmingdaixing", "no": "05",
        "name": "《连名带姓》", "plain": "连名带姓", "year": "2017", "show": 33.0,
        "tag": "名字一被念全，旧伤就醒了",
        "note": "周杰伦谱曲、葛大为填词，成年人式的旧伤复发。",
    },
    {
        "key": "diaole", "clip": "vert_diaole", "no": "04",
        "name": "《掉了》", "plain": "掉了", "year": "2009", "show": 28.0,
        "tag": "失去之后，整个人慢慢被掏空",
        "note": "阿密特时期，唱得更冷、也更撕裂。",
    },
    {
        "key": "jianai", "clip": "vert_jianai", "no": "03",
        "name": "《剪爱》", "plain": "剪爱", "year": "1996", "show": 26.0,
        "tag": "太痛了，只能亲手剪断",
        "note": "成名作的狠：不再追问，开始处理伤口。",
    },
    {
        "key": "wohenwoaini", "clip": "vert_wohenwoaini", "no": "02",
        "name": "《我恨我爱你》", "plain": "我恨我爱你", "year": "2001", "show": 33.0,
        "tag": "恨的不是你，是还爱着的自己",
        "note": "答案早就清楚，却怎么也放不下。",
    },
    {
        "key": "renzhi", "clip": "vert_renzhi", "no": "01",
        "name": "《人质》", "plain": "人质", "year": "2006", "show": 40.0,
        "tag": "被一段互相消耗的关系困住",
        "note": "明知相爱成了消耗，却舍不得挣扎。",
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "cta.wav")
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
cta_start_local = q(LEAD + d_outro + CTA_GAP)
total = q(outro_start + cta_start_local + d_cta + OUTRO_TAIL)


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
cta_delay = int(cta_start_local * 1000)
run([
    "ffmpeg", "-v", "error",
    "-i", f"{C}/{OUTRO_CLIP}.mp4",
    "-i", f"{A}/outro.wav",
    "-i", f"{A}/cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={cta_delay}|{cta_delay},volume={VOICE_GAIN}[vc];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.15,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-OUTRO_TAIL}:d={OUTRO_TAIL}[music];"
    f"[vo][vc][music]amix=inputs=3:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
planned_total = total
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)

# ---- realign visual timeline to ACTUAL segment durations (防音画累积漂移) ----
intro_end = dur(ROOT / "seg_intro.wav")
cur = intro_end
for b in blocks:
    pre_off = LEAD + b["voice_dur"] + 0.25 + DIG
    seg_actual = dur(ROOT / f"seg_{b['key']}.wav")
    b["start"] = q(cur)
    b["full_start"] = q(cur + pre_off)
    b["end"] = q(cur + seg_actual)
    cur = q(cur + seg_actual)
outro_start = q(cur)
assert abs(cur + dur(ROOT / "seg_outro.wav") - total) < 0.05, "timeline mismatch"


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
    for n, name in [("01", "人质"), ("02", "我恨我爱你"), ("03", "剪爱"), ("04", "掉了"), ("05", "连名带姓")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0710;color:#f4eef2;
  font-family:'Noto Sans SC',sans-serif;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a0710}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(10,7,16,.84),rgba(10,7,16,.10) 30%,rgba(10,7,16,.18) 56%,rgba(10,7,16,.88))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 42%,transparent 50%,rgba(5,3,9,.58) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.09;background:repeating-linear-gradient(0deg,rgba(255,255,255,.13) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
/* cover */
#cover{position:absolute;inset:0;z-index:5;padding:150px 76px 142px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;letter-spacing:.12em;color:#e08aa0}
.eyebrow:before{content:"";width:54px;height:3px;background:#e08aa0;border-radius:99px}
#cover h1{font-family:'Noto Serif SC',serif;font-weight:900;font-size:140px;line-height:1.02;letter-spacing:.02em;
  text-shadow:0 6px 40px rgba(0,0,0,.6);max-width:920px}
#cover h1 em{font-style:normal;color:#f0a7b8}
#cover .sub{margin-top:30px;font-size:37px;line-height:1.5;color:#d8cbd4;font-weight:500;max-width:850px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:920px}
.chips span{border:1px solid rgba(214,112,138,.5);color:#f1cdd7;background:rgba(14,9,18,.5);
  font-size:28px;font-weight:600;padding:12px 20px;border-radius:999px}
/* per-song full label */
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:178px;padding:34px 38px 40px;
  background:linear-gradient(135deg,rgba(9,6,14,.85),rgba(9,6,14,.46));backdrop-filter:blur(3px);
  border-left:7px solid #d6708a;border-radius:6px}
.fullLabel .rk{display:flex;align-items:baseline;gap:18px}
.fullLabel .rkno{font-size:32px;font-weight:900;letter-spacing:.05em;color:#e08aa0}
.fullLabel .rkyr{font-size:25px;font-weight:700;color:#998a93;letter-spacing:.1em}
.fullLabel h2{font-family:'Noto Serif SC',serif;margin-top:14px;font-size:92px;line-height:1.04;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:44px;line-height:1.25;font-weight:800;color:#f0a7b8}
.fullLabel .note{margin-top:14px;font-size:32px;line-height:1.4;font-weight:500;color:#cdc1c9}
.fullLabel.topRank{border-left-color:#ff4d63}
.fullLabel.topRank .rkno,.fullLabel.topRank .tag{color:#ff7384}
/* showcase mini tag */
.miniLabel{position:absolute;z-index:5;top:92px;left:54px;display:flex;align-items:center;gap:16px;
  padding:12px 20px;background:rgba(9,6,14,.64);border:1px solid rgba(214,112,138,.5);border-radius:999px}
.miniLabel span{font-size:42px;font-weight:900;color:#e08aa0}
.miniLabel strong{font-family:'Noto Serif SC',serif;font-size:38px;font-weight:800}
.miniLabel.topRank{border-color:rgba(255,77,99,.66)}
.miniLabel.topRank span{color:#ff7384}
/* outro */
#outro{position:absolute;z-index:5;inset:0;padding:128px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:800;letter-spacing:.14em;color:#e08aa0}
#outro h2{font-family:'Noto Serif SC',serif;margin-top:20px;font-size:64px;line-height:1.18;font-weight:800;max-width:930px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 26px;
  background:rgba(9,6,14,.6);border:1px solid rgba(255,255,255,.1);border-radius:8px}
#outro li span{font-size:34px;font-weight:900;color:#e08aa0}
#outro li:first-child{border-color:rgba(255,77,99,.5);background:rgba(40,8,16,.5)}
#outro li:first-child span{color:#ff7384}
#outro li strong{font-family:'Noto Serif SC',serif;font-size:40px;font-weight:800}
#outro .close{margin-top:32px;font-size:32px;line-height:1.5;color:#d8cbd4;font-weight:500;max-width:920px}
/* fixed CTA bar */
#ctaBar{position:absolute;z-index:6;left:60px;right:60px;bottom:120px;padding:36px 40px 40px;text-align:center;
  background:linear-gradient(135deg,rgba(214,112,138,.18),rgba(9,6,14,.88));border:1px solid rgba(214,112,138,.6);
  border-radius:16px;box-shadow:0 18px 60px rgba(0,0,0,.5)}
#ctaBar .q{font-size:48px;line-height:1.2;font-weight:900;color:#f4eef2}
#ctaBar .q b{color:#e08aa0}
#ctaBar .acts{margin-top:22px;display:flex;justify-content:center;gap:30px;font-size:36px;font-weight:800;color:#f1cdd7}
#ctaBar .acts span{display:inline-flex;align-items:center;gap:8px}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="5"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.3)}" data-track-index="2">'
    '<div><div class="eyebrow">情歌天后最苦的一面</div>'
    '<h1>张惠妹<br>最苦的<em>5</em>首歌</h1>'
    '<p class="sub">她的嗓子能扛住最大的情绪，可她最苦的歌，反而都唱得很克制——把放不下，藏在每一个不挣扎的瞬间里。</p></div>'
    '<div class="chips"><span>越克制越疼</span><span>阿密特的冷</span><span>遗憾天花板</span><span>旧伤复发</span><span>被困住的爱</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最 苦 榜 单</div><h2>她最苦的，从来不是声嘶力竭，<br>是克制底下，那一句没说出口的放不下。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：连名带姓、掉了、剪爱、我恨我爱你、人质。</p></section>'
)
cta_abs = q(outro_start + cta_start_local)
body += (
    f'\n<section id="ctaBar" class="clip" data-start="{q(cta_abs-0.3)}" data-duration="{q(total-cta_abs+0.3)}" data-track-index="8">'
    '<div class="q">你最想为哪一首<b>投票</b>？</div>'
    '<div class="acts"><span>♥ 点赞</span><span>★ 收藏</span><span>＋ 关注</span></div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1,y:0}},0);
tl.to("#cover h1",{{scale:1.02,transformOrigin:"left center",duration:4.5,yoyo:true,repeat:1,ease:"sine.inOut"}},1.2);
tl.to("#cover .chips span",{{y:-4,duration:1.4,ease:"sine.inOut",stagger:.08,yoyo:true,repeat:1}},2.0);
tl.to("#cover",{{opacity:0,duration:.45,ease:"power1.in"}},{q(intro_end-.6)});
tl.set("#cover",{{opacity:0}},{q(intro_end-.1)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:20,opacity:0,duration:.55,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:38,opacity:0,duration:.7,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-30,opacity:0,duration:.5,ease:"power2.out",stagger:.12}},{q(outro_start+1.25)});
tl.from("#outro .close",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+2.2)});
tl.to("#outro .close",{{opacity:0,duration:.4,ease:"power1.in"}},{q(cta_abs-0.45)});
tl.set("#outro .close",{{opacity:0}},{q(cta_abs-0.05)});
tl.from("#ctaBar",{{y:34,opacity:0,duration:.5,ease:"power3.out"}},{q(cta_abs-0.3)});
tl.from("#ctaBar .acts span",{{y:14,opacity:0,duration:.4,ease:"power2.out",stagger:.09}},{q(cta_abs+0.25)});
tl.to("#ctaBar,#outro ol,#outro h2,#outro .small",{{opacity:0,duration:1.2,ease:"power1.in"}},{q(total-1.3)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=Noto+Serif+SC:wght@600;700;900&display=swap" rel="stylesheet">
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "amei-saddest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
