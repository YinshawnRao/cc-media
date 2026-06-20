#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 金海心最被低估的5首歌."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 31.0
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
CTA_GAP = 1.0
OUTRO_TAIL = 1.8
INTRO_CLIP = "vert_p2_sleep"
OUTRO_CLIP = "vert_p1_right"


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
        "key": "p5_laibuji", "clip": "vert_p5_laibuji", "no": "05",
        "name": "《来不及》", "plain": "来不及",
        "tag": "慢半拍才意识到失去",
        "note": "被《那么骄傲》专辑光芒盖住的耐听遗珠",
    },
    {
        "key": "p4_bitian", "clip": "vert_p4_bitian", "no": "04",
        "name": "《比天空还远的季节》", "plain": "比天空还远的季节",
        "tag": "安静、内向、远远的孤独",
        "note": "《独立日》里更适合夜里重听的一首",
    },
    {
        "key": "p3_duian", "clip": "vert_p3_duian", "no": "03",
        "name": "《对岸》", "plain": "对岸",
        "tag": "看得见，却很难抵达",
        "note": "透明声线唱有距离的情绪，后劲更深",
    },
    {
        "key": "p2_sleep", "clip": "vert_p2_sleep", "no": "02",
        "name": "《睡不着的海》", "plain": "睡不着的海",
        "tag": "海、夜与不安",
        "note": "早期被标题曲压住的氛围宝藏",
    },
    {
        "key": "p1_right", "clip": "vert_p1_right", "no": "01",
        "name": "《右手戒指》", "plain": "右手戒指",
        "tag": "明亮的自我解放",
        "note": "《独立日》第二波概念主打，却很少被路人提起",
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
    end = q(full_start + SHOW)
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
    out = f"seg_{b['key']}.wav"
    run([
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{b['clip']}.mp4",
        "-i", f"{A}/{b['key']}.wav",
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
boundaries = [intro_end]
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
    tweens.append(f'tl.fromTo("#{fid} .rank",{{x:-36,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power3.out"}},{q(b["start"]+.16)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:46,opacity:0,scale:.98}},{{y:0,opacity:1,scale:1,duration:.68,ease:"expo.out"}},{q(b["start"]+.34)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{x:24,opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power2.out"}},{q(b["start"]+.82)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"sine.out"}},{q(b["start"]+1.08)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.48,ease:"power3.out"}},{q(b["full_start"]+.1)});')
    boundaries.append(b["end"])

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("01", "右手戒指"), ("02", "睡不着的海"), ("03", "对岸"),
        ("04", "比天空还远的季节"), ("05", "来不及"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07090b;font-family:system-ui,sans-serif;color:#f4efe4}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07090b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:radial-gradient(circle at 18% 18%,rgba(216,175,95,.26),rgba(216,175,95,0) 38%),linear-gradient(to bottom,rgba(7,9,11,.78),rgba(7,9,11,.08) 34%,rgba(7,9,11,.24) 62%,rgba(7,9,11,.88))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.14;background:repeating-linear-gradient(0deg,rgba(244,239,228,.16) 0 1px,transparent 1px 5px)}
#veil{position:absolute;inset:-180px;z-index:8;opacity:0;pointer-events:none;background:radial-gradient(circle at 20% 40%,rgba(216,175,95,.58),rgba(216,175,95,0) 34%),radial-gradient(circle at 80% 55%,rgba(184,201,199,.42),rgba(184,201,199,0) 30%);filter:blur(22px)}
#cover{position:absolute;inset:0;z-index:5;padding:154px 70px 132px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:800;color:#d8af5f;letter-spacing:.08em}
.eyebrow:before{content:"";width:58px;height:4px;background:#d8af5f;border-radius:99px}
#cover h1{margin-top:34px;font-family:serif;font-size:118px;line-height:1.08;font-weight:900;max-width:930px;text-shadow:0 10px 46px rgba(0,0,0,.58)}
#cover .sub{margin-top:34px;font-size:38px;line-height:1.48;color:#d8e0dc;font-weight:650;max-width:870px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(216,175,95,.58);color:#f0d99e;background:rgba(20,26,30,.58);font-size:29px;font-weight:750;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:62px;right:62px;bottom:178px;padding:34px 36px 40px;background:linear-gradient(135deg,rgba(7,9,11,.86),rgba(16,46,53,.54));border-left:8px solid #d8af5f;border-radius:6px;box-shadow:0 24px 80px rgba(0,0,0,.48)}
.fullLabel .rank{font-family:monospace;font-size:31px;font-weight:800;color:#d8af5f;letter-spacing:.03em}
.fullLabel h2{margin-top:14px;font-family:serif;font-size:78px;line-height:1.08;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:41px;line-height:1.28;font-weight:800;color:#efd493}
.fullLabel .note{margin-top:13px;font-size:30px;line-height:1.42;font-weight:560;color:#c9d4d1}
.fullLabel.topRank{border-left-color:#d96d63}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff9488}
.miniLabel{position:absolute;z-index:5;top:94px;left:56px;display:flex;align-items:center;gap:16px;padding:13px 19px;background:rgba(7,9,11,.70);border:1px solid rgba(216,175,95,.60);border-radius:8px}
.miniLabel span{font-family:monospace;font-size:43px;font-weight:800;color:#d8af5f}
.miniLabel strong{font-size:36px;font-weight:800}
.miniLabel.topRank{border-color:rgba(217,109,99,.72)}
.miniLabel.topRank span{color:#ff9488}
#outro{position:absolute;z-index:5;inset:0;padding:132px 70px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:800;color:#d8af5f;letter-spacing:.08em}
#outro h2{margin-top:18px;font-family:serif;font-size:66px;line-height:1.16;font-weight:900;max-width:930px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:17px 23px;background:rgba(7,9,11,.64);border:1px solid rgba(244,239,228,.14);border-radius:8px}
#outro li span{font-family:monospace;font-size:33px;font-weight:800;color:#d8af5f}
#outro li:first-child{border-color:rgba(217,109,99,.55)}
#outro li:first-child span{color:#ff9488}
#outro li strong{font-size:34px;font-weight:800;text-align:right}
#outro .close{margin-top:31px;font-size:32px;line-height:1.46;color:#d8e0dc;font-weight:620}
#ctaBar{position:absolute;z-index:6;left:58px;right:58px;bottom:112px;padding:34px 38px 38px;text-align:center;background:linear-gradient(135deg,rgba(216,175,95,.20),rgba(7,9,11,.88));border:1px solid rgba(216,175,95,.64);border-radius:16px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar .q{font-size:47px;line-height:1.22;font-weight:900;color:#f4efe4}
#ctaBar .q b{color:#d8af5f}
#ctaBar .acts{margin-top:21px;display:flex;justify-content:center;gap:28px;font-size:35px;font-weight:800;color:#efd493}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7" data-layout-ignore></div>'
body += f'\n<div id="veil" class="clip" data-start="0" data-duration="{total}" data-track-index="8" data-layout-ignore></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">被大热盖住的透明声线</div><h1>金海心最被低估的5首歌</h1>'
    '<p class="sub">不先公布完整名单。从第五名开始，听那些被专辑光芒压住、却越听越有后劲的歌。</p></div>'
    '<div class="chips"><span>专辑遗珠</span><span>透明感声线</span><span>夜里重听</span><span>被低估的明亮</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">完整榜单</div><h2>这些歌不一定最大声，却最能听见金海心声音里的光。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：来不及、比天空还远的季节、对岸、睡不着的海、右手戒指。</p></section>'
)
cta_abs = q(outro_start + cta_start_local)
body += (
    f'\n<section id="ctaBar" class="clip" data-start="{q(cta_abs-0.3)}" data-duration="{q(total-cta_abs+0.3)}" data-track-index="5">'
    '<div class="q">你最想为哪一首<b>投票</b>？</div>'
    '<div class="acts"><span>点赞</span><span>收藏</span><span>关注</span></div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

transition_tweens = []
for boundary in boundaries[:-1]:
    if boundary > 0.8:
        transition_tweens.append(
            f'tl.fromTo("#veil",{{opacity:0,x:-360}},{{opacity:.62,x:360,duration:.55,ease:"sine.inOut",immediateRender:false,overwrite:"auto"}},{q(boundary-.25)});'
        )
        transition_tweens.append(f'tl.to("#veil",{{opacity:0,duration:.32,ease:"power1.out",overwrite:"auto"}},{q(boundary+.28)});')

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1,y:0}},0);
tl.to("#cover h1",{{scale:1.016,transformOrigin:"left center",duration:3.1,ease:"sine.inOut",yoyo:true,repeat:1}},1.2);
tl.to("#cover .chips span",{{y:-4,duration:1.35,ease:"sine.inOut",stagger:.08,yoyo:true,repeat:1}},2.1);
tl.to("#cover",{{opacity:0,duration:.45,ease:"power1.in"}},{q(intro_end-.58)});
tl.set("#cover",{{opacity:0}},{q(intro_end-.1)});
{chr(10).join(transition_tweens)}
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{x:-24,opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power3.out"}},{q(outro_start+.25)});
tl.fromTo("#outro h2",{{y:42,opacity:0}},{{y:0,opacity:1,duration:.7,ease:"expo.out"}},{q(outro_start+.58)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out",stagger:.1}},{q(outro_start+1.22)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"sine.out"}},{q(outro_start+2.1)});
tl.to("#outro .close",{{opacity:0,duration:.4,ease:"power1.in"}},{q(cta_abs-0.45)});
tl.set("#outro .close",{{opacity:0,visibility:"hidden"}},{q(cta_abs-0.05)});
tl.fromTo("#ctaBar",{{y:34,opacity:0}},{{y:0,opacity:1,duration:.52,ease:"power3.out"}},{q(cta_abs-0.3)});
tl.fromTo("#ctaBar .acts span",{{y:14,opacity:0}},{{y:0,opacity:1,duration:.38,ease:"power2.out",stagger:.09}},{q(cta_abs+0.25)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "jinhaixin-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
