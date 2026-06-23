#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 陈奕迅最苦的5首歌."""
import contextlib
import json
import subprocess
import wave

from project import (
    AUDIO,
    BED,
    CLIPS,
    CTA_GAP,
    DIG,
    INTRO_GAP,
    INTRO_VOICE_START,
    ITEMS,
    LEAD,
    OUTRO_TAIL,
    RANKING_ROWS,
    ROOT,
    SLUG,
    TITLE,
    VOICE_GAIN,
)


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

d_intro = dur(AUDIO / "intro.wav")
d_outro = dur(AUDIO / "outro.wav")
d_cta = dur(AUDIO / "cta.wav")
for item in ITEMS:
    item["voice_dur"] = dur(AUDIO / f"{item['key']}.wav")
    item["narration"] = meta[item["key"]]["text"]

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in ITEMS:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + item["show"])
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start})
    t = q(end)

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
    "-i", f"{CLIPS}/vert_cover.mp4",
    "-i", f"{AUDIO}/intro.wav",
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
    out = f"seg_{b['key']}.wav"
    run([
        "ffmpeg", "-v", "error",
        "-i", f"{CLIPS}/vert_{b['key']}.mp4",
        "-i", f"{AUDIO}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

outro_dur = q(total - outro_start)
cta_delay = int(cta_start_local * 1000)
run([
    "ffmpeg", "-v", "error",
    "-i", f"{CLIPS}/vert_fushi.mp4",
    "-i", f"{AUDIO}/outro.wav",
    "-i", f"{AUDIO}/cta.wav",
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


videos = [video_tag(0, 0, intro_end, "vert_cover")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), f"vert_{b['key']}"))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_fushi"))

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
    tweens.extend([
        f'tl.from("#{fid} .rk",{{y:26,opacity:0,duration:.5,ease:"power2.out"}},{q(b["start"]+.18)});',
        f'tl.from("#{fid} h2",{{y:46,opacity:0,duration:.7,ease:"power3.out"}},{q(b["start"]+.36)});',
        f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(b["start"]+.74)});',
        f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(b["start"]+.98)});',
        f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{q(b["full_start"]-.45)});',
        f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});',
        f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.5,ease:"power2.out"}},{q(b["full_start"]+.12)});',
        f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["end"]-.4)});',
        f'tl.set("#{mid}",{{opacity:0}},{q(b["end"])});',
    ])

ranking_rows = "".join(f'<li><span>{n}</span><strong>{name}</strong></li>' for n, name in RANKING_ROWS)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#09090b;color:#f7f3ee;
  font-family:'PingFang SC','Hiragino Sans GB','Noto Sans SC',sans-serif;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#09090b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,8,11,.84),rgba(8,8,11,.10) 28%,rgba(8,8,11,.18) 58%,rgba(8,8,11,.88))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 42%,transparent 48%,rgba(0,0,0,.62) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.08;background:repeating-linear-gradient(0deg,rgba(255,255,255,.12) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:148px 74px 136px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;letter-spacing:.12em;color:#d5b277}
.eyebrow:before{content:"";width:54px;height:3px;background:#d5b277;border-radius:99px}
#cover h1{font-family:'Songti SC','Noto Serif SC',serif;font-weight:900;font-size:138px;line-height:1.02;letter-spacing:0;text-shadow:0 6px 40px rgba(0,0,0,.62);max-width:930px}
#cover h1 em{font-style:normal;color:#e8c987}
#cover .sub{margin-top:30px;font-size:37px;line-height:1.5;color:#ded8ce;font-weight:500;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:940px}
.chips span{border:1px solid rgba(213,178,119,.52);color:#f3dfb3;background:rgba(9,9,11,.52);font-size:28px;font-weight:650;padding:12px 20px;border-radius:999px}
.fullLabel{position:absolute;z-index:5;left:62px;right:62px;bottom:176px;padding:34px 38px 40px;background:linear-gradient(135deg,rgba(8,8,11,.86),rgba(8,8,11,.48));backdrop-filter:blur(3px);border-left:7px solid #d5b277;border-radius:6px}
.fullLabel .rk{display:flex;align-items:baseline;gap:18px}
.fullLabel .rkno{font-size:32px;font-weight:900;letter-spacing:.05em;color:#d5b277}
.fullLabel .rkyr{font-size:25px;font-weight:750;color:#a79d8f;letter-spacing:.1em}
.fullLabel h2{font-family:'Songti SC','Noto Serif SC',serif;margin-top:14px;font-size:90px;line-height:1.05;font-weight:900;letter-spacing:0}
.fullLabel .tag{margin-top:20px;font-size:43px;line-height:1.25;font-weight:850;color:#f0d99c}
.fullLabel .note{margin-top:14px;font-size:32px;line-height:1.42;font-weight:500;color:#d6d0c7}
.fullLabel.topRank{border-left-color:#f1c65c}
.fullLabel.topRank .rkno,.fullLabel.topRank .tag{color:#ffd46a}
.miniLabel{position:absolute;z-index:5;top:92px;left:54px;display:flex;align-items:center;gap:16px;padding:12px 20px;background:rgba(8,8,11,.66);border:1px solid rgba(213,178,119,.56);border-radius:999px}
.miniLabel span{font-size:42px;font-weight:900;color:#d5b277}
.miniLabel strong{font-family:'Songti SC','Noto Serif SC',serif;font-size:38px;font-weight:850}
.miniLabel.topRank{border-color:rgba(255,212,106,.68)}
.miniLabel.topRank span{color:#ffd46a}
#outro{position:absolute;z-index:5;inset:0;padding:128px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;letter-spacing:.14em;color:#d5b277}
#outro h2{font-family:'Songti SC','Noto Serif SC',serif;margin-top:20px;font-size:64px;line-height:1.18;font-weight:850;max-width:930px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 26px;background:rgba(8,8,11,.62);border:1px solid rgba(255,255,255,.1);border-radius:8px}
#outro li span{font-size:34px;font-weight:900;color:#d5b277}
#outro li:first-child{border-color:rgba(255,212,106,.52);background:rgba(51,38,12,.48)}
#outro li:first-child span{color:#ffd46a}
#outro li strong{font-family:'Songti SC','Noto Serif SC',serif;font-size:40px;font-weight:850}
#outro .close{margin-top:32px;font-size:32px;line-height:1.5;color:#ded8ce;font-weight:500;max-width:920px}
#ctaBar{position:absolute;z-index:6;left:60px;right:60px;bottom:120px;padding:36px 40px 40px;text-align:center;background:linear-gradient(135deg,rgba(213,178,119,.18),rgba(8,8,11,.88));border:1px solid rgba(213,178,119,.62);border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar .q{font-size:48px;line-height:1.2;font-weight:900;color:#f7f3ee}
#ctaBar .q b{color:#f0d99c}
#ctaBar .acts{margin-top:22px;display:flex;justify-content:center;gap:30px;font-size:36px;font-weight:850;color:#f3dfb3}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="5"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.3)}" data-track-index="2">'
    '<div><div class="eyebrow">苦情不是撕裂，是忍住</div>'
    '<h1>陈奕迅<br>最苦的<em>5</em>首歌</h1>'
    '<p class="sub">他最狠的情歌，常常不是唱崩溃，而是唱一个人终于承认：有些山，真的搬不走。</p></div>'
    '<div class="chips"><span>爱而不得</span><span>余生感</span><span>关系空城</span><span>友情走散</span><span>人生苦味</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最 苦 榜 单</div><h2>陈奕迅最苦的，往往不是让你哭出来，<br>是很多年后突然懂了自己为什么放不下。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：葡萄成熟时、最佳损友、人来人往、明年今日、富士山下。</p></section>'
)
cta_abs = q(outro_start + cta_start_local)
body += (
    f'\n<section id="ctaBar" class="clip" data-start="{q(cta_abs-0.3)}" data-duration="{q(total-cta_abs+0.3)}" data-track-index="8">'
    '<div class="q">你最想为哪一首<b>投票</b>？</div>'
    '<div class="acts"><span>点赞</span><span>收藏</span><span>关注</span></div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1,y:0}},0);
tl.to("#cover h1",{{scale:1.018,transformOrigin:"left center",duration:4.2,yoyo:true,repeat:1,ease:"sine.inOut"}},.4);
tl.to("#cover .chips span",{{y:-4,duration:1.35,ease:"sine.inOut",stagger:.08,yoyo:true,repeat:1}},1.5);
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
  <script src="vendor/gsap.min.js"></script>
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": SLUG, "title": TITLE}, ensure_ascii=False), encoding="utf-8")
(ROOT / "timeline.json").write_text(json.dumps({"total": total, "intro_end": intro_end, "outro_start": outro_start, "blocks": blocks}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])

