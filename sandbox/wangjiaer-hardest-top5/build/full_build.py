#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 王嘉尔最难的5首歌."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

LEAD = 0.35
BED = 0.14
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.3
OUTRO_TAIL = 2.8
MGAIN = {
    "p5_come_alive": 1.05,
    "p4_lmly": 1.03,
    "p3_cruel": 1.05,
    "p2_blow": 1.10,
    "p1_made": 1.00,
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
        "key": "p5_come_alive",
        "clip": "vert_come_alive",
        "no": "05",
        "name": "《Come Alive》",
        "plain": "Come Alive",
        "tag": "爵士、摇滚和R&B的混合律动",
        "note": "磁性低位和高位释放要来回切换",
        "chorus": 23.06,
        "show": 38.0,
    },
    {
        "key": "p4_lmly",
        "clip": "vert_lmly",
        "no": "04",
        "name": "《LMLY》",
        "plain": "LMLY",
        "tag": "越轻松，越全是控制",
        "note": "气声、轻混、咬字和尾音都不能松",
        "chorus": 22.60,
        "show": 38.0,
    },
    {
        "key": "p3_cruel",
        "clip": "vert_cruel",
        "no": "03",
        "name": "《Cruel》",
        "plain": "Cruel",
        "tag": "狠要有控制，不能真伤嗓",
        "note": "暗黑张力、烟嗓、音准同时在线",
        "chorus": 18.40,
        "show": 38.0,
    },
    {
        "key": "p2_blow",
        "clip": "vert_blow",
        "no": "02",
        "name": "《Blow》",
        "plain": "Blow",
        "tag": "摇滚烟嗓的代表性考题",
        "note": "唱轻没冲击，唱重容易真哑",
        "chorus": 21.48,
        "show": 40.0,
    },
    {
        "key": "p1_made",
        "clip": "vert_made",
        "no": "01",
        "name": "《Made Me a Man》",
        "plain": "Made Me a Man",
        "tag": "破碎感、头声和情绪爆发并存",
        "note": "脆弱不能散，爆发也要稳",
        "chorus": 22.71,
        "show": 44.0,
    },
]

intro_dur = q(INTRO_VOICE_START + dur(A / "intro.wav") + INTRO_GAP)
t = intro_dur
blocks = []
for item in items:
    voice_dur = dur(A / f"{item['key']}.wav")
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + voice_dur)
    full_start = q(t + item["chorus"])
    if full_start <= narr_end + 0.55:
        raise RuntimeError(f"{item['key']} chorus offset leaves no breathing room after narration")
    end = q(full_start + item["show"])
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "voice_dur": voice_dur, "full_start": full_start})
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + dur(A / "outro.wav"))
planned_total = q(outro_voice_end + OUTRO_TAIL)


def envelope(narr_end_local, full_start_local):
    swell_start = q(narr_end_local + 0.25)
    ramp = max(0.45, q(full_start_local - swell_start))
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell_start}))*{BED}"
        f"+(between(t,{swell_start},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell_start})/{ramp})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_made.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.22,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.45}:d=0.45[music];"
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
    full_start_local = b["chorus"]
    env = envelope(narr_end_local, full_start_local)
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
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.90:level=false[out]",
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

outro_dur = q(planned_total - outro_start)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_made.mp4",
        "-i",
        f"{A}/outro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.20,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-0.45}:d=0.45[music];"
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
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_dur, "vert_made")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_made"))

labels = []
tweens = []
for idx, b in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    top_class = " topRank" if b["no"] == "01" else ""
    full_track = 2 if idx % 2 == 0 else 8
    mini_track = 4 if idx % 2 == 0 else 9
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{top_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="{full_track}">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{top_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="{mini_track}">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.append(f'tl.from("#{fid} .rank",{{y:30,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:46,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.45)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-24,opacity:0,duration:.42,ease:"power2.out"}},{q(b["full_start"]+.08)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "Come Alive"),
        ("04", "LMLY"),
        ("03", "Cruel"),
        ("02", "Blow"),
        ("01", "Made Me a Man"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07070a;font-family:sans-serif;color:#f4f0eb}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
.scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(7,7,10,.72),rgba(7,7,10,.18) 30%,rgba(7,7,10,.24) 55%,rgba(7,7,10,.86))}
.grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background-image:radial-gradient(circle at 20% 20%,#fff 0 1px,transparent 1px),radial-gradient(circle at 70% 40%,#fff 0 1px,transparent 1px);background-size:38px 38px,53px 53px;mix-blend-mode:screen}
#cover{position:absolute;left:70px;right:70px;bottom:250px;z-index:5}
#cover .eyebrow{display:flex;align-items:center;gap:18px;color:#f0b35b;font-size:30px;font-weight:800}
#cover .eyebrow::before{content:"";display:block;width:54px;height:5px;background:#ff2f4f;border-radius:3px}
#cover h1{margin-top:34px;font-size:128px;line-height:1.02;font-weight:900;color:#fff;text-shadow:0 14px 50px rgba(0,0,0,.55)}
#cover .accent{display:block;color:#ff2f4f}
#cover .desc{margin-top:30px;max-width:830px;font-size:40px;line-height:1.42;font-weight:650;color:#d9d4cf}
.fullLabel{position:absolute;left:72px;right:72px;bottom:238px;z-index:5;color:#fff}
.fullLabel .rank{display:inline-flex;align-items:center;height:54px;padding:0 24px;border:2px solid rgba(255,47,79,.78);border-radius:999px;background:rgba(7,7,10,.45);color:#ff5e75;font-size:30px;font-weight:900}
.fullLabel h2{margin-top:22px;font-size:84px;line-height:1.08;font-weight:900;max-width:900px;text-shadow:0 12px 44px rgba(0,0,0,.7)}
.fullLabel .tag{margin-top:20px;color:#f0b35b;font-size:38px;line-height:1.32;font-weight:800}
.fullLabel .note{margin-top:12px;color:#d9d4cf;font-size:31px;line-height:1.38;font-weight:650;max-width:850px}
.fullLabel.topRank .rank{background:#ff2f4f;color:#fff;box-shadow:0 0 34px rgba(255,47,79,.45)}
.miniLabel{position:absolute;top:116px;left:62px;z-index:5;display:flex;align-items:center;gap:18px;color:#fff;padding:12px 20px 13px 18px;background:rgba(7,7,10,.62);border-left:6px solid #ff2f4f;backdrop-filter:blur(8px)}
.miniLabel span{font-size:46px;font-weight:950;color:#ff5e75}
.miniLabel strong{font-size:41px;font-weight:880}
.miniLabel.topRank{border-left-color:#f0b35b}
#outro{position:absolute;left:70px;right:70px;top:220px;bottom:170px;z-index:5;display:flex;flex-direction:column;justify-content:center}
#outro .kicker{color:#f0b35b;font-size:32px;font-weight:900}
#outro h2{margin-top:28px;font-size:78px;line-height:1.12;font-weight:950;color:#fff}
#outro ul{margin-top:42px;list-style:none;display:flex;flex-direction:column;gap:18px}
#outro li{display:flex;align-items:center;gap:24px;font-size:42px;font-weight:850;color:#f4f0eb}
#outro li span{width:76px;color:#ff2f4f;font-size:50px;font-weight:950}
#outro .final{margin-top:44px;color:#d9d4cf;font-size:34px;line-height:1.42;font-weight:650}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip scrim" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip grain" data-start="0" data-duration="{total}" data-track-index="5"></div>'
body += f"""
<section id="cover" class="clip" data-start="0.25" data-duration="{q(intro_dur - 0.55)}" data-track-index="2">
  <div class="eyebrow">声乐难度盘点</div>
  <h1>王嘉尔<br><span class="accent">最难的5首歌</span></h1>
  <p class="desc">不只看高音，也看烟嗓、气息、真假声切换、律动和情绪控制。</p>
</section>
"""
body += "\n".join(labels)
body += f"""
<section id="outro" class="clip" data-start="{outro_voice}" data-duration="{q(total - outro_voice)}" data-track-index="4">
  <div class="kicker">最终排名</div>
  <h2>越接近失控，<br>越考验控制。</h2>
  <ul>{ranking_rows}</ul>
  <p class="final">粗粝、脆弱、性感、律动和爆发，都要同时成立。</p>
</section>
"""
body += f'<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.from("#cover .eyebrow",{{x:-34,opacity:0,duration:.5,ease:"power2.out"}},0.45);
tl.from("#cover h1",{{y:64,opacity:0,duration:.75,ease:"power4.out"}},0.78);
tl.from("#cover .desc",{{y:26,opacity:0,duration:.55,ease:"power2.out"}},1.25);
tl.to("#cover",{{opacity:0,duration:.45,ease:"power1.in"}},{q(intro_dur-.65)});
{chr(10).join(tweens)}
tl.from("#outro .kicker",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_voice+.2)});
tl.from("#outro h2",{{y:44,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_voice+.55)});
tl.from("#outro li",{{x:-30,opacity:0,duration:.45,ease:"power2.out",stagger:.11}},{q(outro_voice+1.15)});
tl.from("#outro .final",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_voice+2.05)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "wangjiaer-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
(ROOT / "timeline.json").write_text(json.dumps({"total": total, "intro": intro_dur, "blocks": blocks, "outro_start": outro_start}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "blocks:", [(b["key"], b["start"], b["full_start"], b["end"]) for b in blocks])
