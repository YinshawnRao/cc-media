#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Tian Fuzhen hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 40.0
LEAD = 0.35
DIG = 1.55
BED = 0.14
VOICE_GAIN = 2.0
MGAIN = {
    "p4_xuanri": 1.12,
    "p1_fengci": 1.55,
}
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.2
BETWEEN = 0.0
OUTRO_TAIL = 2.6


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
        "key": "p5_maodun",
        "clip": "vert_maodun",
        "no": "05",
        "name": "《矛盾》",
        "plain": "矛盾",
        "tag": "摇滚张力里，还要保持清透",
        "note": "持续推进、音准咬字、冲突感都要稳",
    },
    {
        "key": "p4_xuanri",
        "clip": "vert_xuanri",
        "no": "04",
        "name": "《悬日》",
        "plain": "悬日",
        "tag": "轻轻唱，但气息不能散",
        "note": "漂浮感、支撑感、句尾连接都很细",
    },
    {
        "key": "p3_mogui",
        "clip": "vert_mogui",
        "no": "03",
        "name": "《魔鬼中的天使》",
        "plain": "魔鬼中的天使",
        "tag": "爆发和危险感要同时存在",
        "note": "副歌穿透，主歌轻声，不能失控",
    },
    {
        "key": "p2_buyao",
        "clip": "vert_buyao",
        "no": "02",
        "name": "《你就不要想起我》",
        "plain": "你就不要想起我",
        "tag": "越推越高，还要清亮克制",
        "note": "长句、尾音、逞强感都不能塌",
    },
    {
        "key": "p1_fengci",
        "clip": "vert_fengci",
        "no": "01",
        "name": "《讽刺的情书》",
        "plain": "讽刺的情书",
        "tag": "绵密字句里的冷静隐痛",
        "note": "速度感切换、音域跨度、情绪打开都很硬",
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
    end = q(full_start + SHOW)
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start})
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
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_maodun.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.11,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
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
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_fengci.mp4",
        "-i",
        f"{A}/outro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.25}:d=1.25[music];"
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


videos = [video_tag(0, 0, intro_end, "vert_maodun")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_fengci"))

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
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "讽刺的情书"), ("02", "你就不要想起我"), ("03", "魔鬼中的天使"), ("04", "悬日"), ("05", "矛盾")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08080b;font-family:sans-serif;color:#f6f1ec;letter-spacing:0}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08080b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.76),rgba(0,0,0,.16) 32%,rgba(0,0,0,.2) 58%,rgba(0,0,0,.8))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:160px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#d8b06a}
.eyebrow:before{content:"";width:52px;height:4px;background:#d8b06a;border-radius:99px}
#cover h1{font-size:126px;line-height:1.04;font-weight:950;max-width:900px}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.45;color:#ddd5ce;font-weight:650;max-width:850px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:860px}
.chips span{border:1px solid rgba(216,176,106,.56);color:#f3d8a7;background:rgba(8,8,12,.52);font-size:28px;font-weight:750;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(7,7,11,.82),rgba(7,7,11,.48));border-left:8px solid #d8b06a}
.fullLabel .rank{font-size:30px;font-weight:900;color:#d8b06a}
.fullLabel h2{margin-top:14px;font-size:82px;line-height:1.06;font-weight:950}
.fullLabel .tag{margin-top:18px;font-size:42px;line-height:1.28;font-weight:850;color:#f0d197}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#d1c9c2}
.fullLabel.topRank{border-left-color:#e45d73}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff7c92}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;max-width:910px;padding:12px 18px;background:rgba(7,7,11,.68);border:1px solid rgba(216,176,106,.58);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#d8b06a}
.miniLabel strong{font-size:36px;font-weight:900;white-space:nowrap}
.miniLabel.topRank{border-color:rgba(228,93,115,.72)}
.miniLabel.topRank span{color:#ff7c92}
#outro{position:absolute;z-index:5;inset:0;padding:150px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#d8b06a}
#outro h2{margin-top:18px;font-size:72px;line-height:1.13;font-weight:950;max-width:900px}
#outro ol{margin-top:44px;list-style:none;display:grid;gap:16px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:18px 22px;background:rgba(7,7,11,.62);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#d8b06a}
#outro li:first-child span{color:#ff7c92}
#outro li strong{font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.45;color:#ddd5ce;font-weight:650}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>田馥甄<br>最难的5首歌</h1>'
    '<p class="sub">不是只比谁唱得高，而是看冷静、气息、细腻和爆发，能不能在同一首歌里同时成立。</p></div>'
    '<div class="chips"><span>高位推进</span><span>气息线</span><span>音色控制</span><span>情绪克制</span><span>绵密咬字</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>田馥甄的难，是情绪快满出来了，声音还要清醒。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期按难度从第一到第五收束：讽刺的情书、你就不要想起我、魔鬼中的天使、悬日、矛盾。</p></section>'
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
"""

html = f"""<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>"""

(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "tianfuzhen-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "s", "blocks:", [(b["key"], b["start"], b["end"]) for b in blocks], "outro:", outro_start, total)
