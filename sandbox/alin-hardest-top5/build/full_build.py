#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for A-Lin hardest top 5."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW_DEFAULT = 36.0
SHOW_MAP = {
    "p5_guilty": 32.0,
    "p4_sorrow": 34.0,
    "p3_happiness": 34.0,
}
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 0.0
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
MGAIN = {
    "p1_reason": 1.08,
    "p2_tian": 1.05,
}


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


items = [
    {
        "key": "p5_guilty",
        "clip": "vert_guilty",
        "no": "05",
        "name": "《失恋无罪》",
        "plain": "失恋无罪",
        "tag": "强声压和情绪爆发",
        "note": "早期招牌歌，厚声线、咬字、爆发都要稳",
    },
    {
        "key": "p4_sorrow",
        "clip": "vert_sorrow",
        "no": "04",
        "name": "《有一种悲伤》",
        "plain": "有一种悲伤",
        "tag": "克制比哭出来更难",
        "note": "不能太满，也不能太平，后段支撑很吃控制",
    },
    {
        "key": "p3_happiness",
        "clip": "vert_happiness",
        "no": "03",
        "name": "《幸福了 然后呢》",
        "plain": "幸福了 然后呢",
        "tag": "长线情绪慢慢堆高",
        "note": "压抑、迷惑、质问，一层一层往上推",
    },
    {
        "key": "p2_tian",
        "clip": "vert_tian",
        "no": "02",
        "name": "《天若有情》",
        "plain": "天若有情",
        "tag": "影视主题曲式的大气场",
        "note": "长句、开阔旋律、宿命感都要撑住",
    },
    {
        "key": "p1_reason",
        "clip": "vert_reason",
        "no": "01",
        "name": "《给我一个理由忘记》",
        "plain": "给我一个理由忘记",
        "tag": "K歌很红，真唱很难",
        "note": "高位持续、长句多，爆发和控制同时在线",
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
    show = SHOW_MAP.get(item["key"], SHOW_DEFAULT)
    end = q(full_start + show)
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start, "show": show})
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
planned_total = q(cta_voice_end + OUTRO_TAIL)


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
    "-i", f"{C}/vert_intro.mp4",
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
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={MGAIN.get(b['key'], 1.0)}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

outro_dur = q(planned_total - outro_start)
cta_local = q(cta_voice - outro_start)
run([
    "ffmpeg", "-v", "error",
    "-i", f"{C}/vert_reason.mp4",
    "-i", f"{A}/outro.wav",
    "-i", f"{A}/outro_cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
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
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_reason"))

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
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{q(b["start"]+.34)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{b["no"]}</span><strong>{b["plain"]}</strong></li>'
    for b in reversed(blocks)
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080c;font-family:"Noto Serif SC","Songti SC","PingFang SC",serif;color:#f8f3ee}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07080c}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(7,8,12,.82),rgba(7,8,12,.18) 34%,rgba(7,8,12,.22) 58%,rgba(7,8,12,.88))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.10;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 5px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:150px 72px 142px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-family:"PingFang SC",sans-serif;font-size:30px;font-weight:850;color:#d9a35f;letter-spacing:.12em}
.eyebrow:before{content:"";width:52px;height:4px;background:#d9a35f;border-radius:99px}
#cover h1{margin-top:30px;font-size:124px;line-height:1.05;font-weight:950;max-width:920px;letter-spacing:0}
#cover .sub{margin-top:30px;font-family:"PingFang SC",sans-serif;font-size:38px;line-height:1.45;color:#cfc4bb;font-weight:650;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{font-family:"PingFang SC",sans-serif;border:1px solid rgba(217,163,95,.58);color:#f1d2ab;background:rgba(7,8,12,.58);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:68px;right:68px;bottom:188px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(7,8,12,.86),rgba(7,8,12,.54));border-left:8px solid #d9a35f}
.fullLabel .rank{font-family:"PingFang SC",sans-serif;font-size:30px;font-weight:900;color:#d9a35f;letter-spacing:.08em}
.fullLabel h2{margin-top:14px;font-size:78px;line-height:1.08;font-weight:950}
.fullLabel .tag{margin-top:18px;font-family:"PingFang SC",sans-serif;font-size:40px;line-height:1.28;font-weight:850;color:#f0c28d}
.fullLabel .note{margin-top:12px;font-family:"PingFang SC",sans-serif;font-size:30px;line-height:1.38;font-weight:650;color:#d4c9bf}
.fullLabel.topRank{border-left-color:#d84a4a}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff6a5c}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(7,8,12,.72);border:1px solid rgba(217,163,95,.62);border-radius:8px}
.miniLabel span{font-family:"PingFang SC",sans-serif;font-size:44px;font-weight:950;color:#d9a35f}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(216,74,74,.82)}
.miniLabel.topRank span{color:#ff6a5c}
#outro{position:absolute;z-index:5;inset:0;padding:142px 72px 240px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-family:"PingFang SC",sans-serif;font-size:32px;font-weight:850;color:#d9a35f;letter-spacing:.1em}
#outro h2{margin-top:18px;font-size:68px;line-height:1.15;font-weight:950;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(7,8,12,.66);border:1px solid rgba(255,255,255,.13);border-radius:8px}
#outro li span{font-family:"PingFang SC",sans-serif;font-size:34px;font-weight:950;color:#d9a35f}
#outro li:first-child span{color:#ff6a5c}
#outro li strong{font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:32px;font-family:"PingFang SC",sans-serif;font-size:31px;line-height:1.45;color:#d8cec5;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:96px;text-align:center}
#cta .v{font-family:"PingFang SC",sans-serif;font-size:46px;font-weight:950;color:#ff6a5c;line-height:1.2}
#cta .f{margin-top:16px;font-family:"PingFang SC",sans-serif;font-size:36px;font-weight:850;color:#d9a35f;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>黄丽玲 A-Lin 最难的5首歌</h1>'
    '<p class="sub">不只比高音。真正难的是大嗓情歌里的细节、长线支撑和情绪控制。</p></div>'
    '<div class="chips"><span>高位持续</span><span>长句气息</span><span>声压控制</span><span>克制情绪</span><span>大歌气场</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>阿林的难，不只是嗓门大，是每一次爆发都还留着控制。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这五首从早期强声压，到电影主题曲的细腻克制，再到压轴的大嗓情歌，刚好串起她最难被模仿的那一面。</p></section>'
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
  <script src="vendor/gsap-lite.js"></script>
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "alin-hardest-top5", "duration": total}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
