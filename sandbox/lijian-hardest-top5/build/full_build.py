#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Li Jian hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 36.0
LEAD = 0.35
DIG = 1.5
BED = 0.14
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.1
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
MGAIN = {
    "p5_meiruo": 1.12,
    "p4_chuanqi": 1.08,
    "p1_baikal": 1.45,
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
        "key": "p5_meiruo",
        "clip": "vert_meiruo",
        "no": "05",
        "name": "《美若黎明》",
        "plain": "美若黎明",
        "tag": "明亮但不能刺，轻盈但不能飘",
        "note": "开阔、轻声、支撑感同时在线",
        "badge": "",
    },
    {
        "key": "p4_chuanqi",
        "clip": "vert_chuanqi",
        "no": "04",
        "name": "《传奇》",
        "plain": "传奇",
        "tag": "简单到没有地方躲",
        "note": "一根旋律线，气息和尾音全被放大",
        "badge": "",
    },
    {
        "key": "p3_xiangwang",
        "clip": "vert_xiangwang",
        "no": "03",
        "name": "《向往》",
        "plain": "向往",
        "tag": "干净、舒展、还要稳",
        "note": "不能唱满，也不能唱软",
        "badge": "",
    },
    {
        "key": "p2_tianyi",
        "clip": "vert_tianyi",
        "no": "02",
        "name": "《假如爱有天意》",
        "plain": "假如爱有天意",
        "tag": "宿命感不能唱成努力感",
        "note": "从轻远到撑开，层层递进",
        "badge": "情绪递进",
    },
    {
        "key": "p1_baikal",
        "clip": "vert_baikal",
        "no": "01",
        "name": "《贝加尔湖畔》",
        "plain": "贝加尔湖畔",
        "tag": "高位弱声，轻而不虚",
        "note": "气息、空灵感和长线条的终极考验",
        "badge": "",
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
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


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
        f"{C}/vert_meiruo.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
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
cta_local = q(cta_voice - outro_start)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_baikal.mp4",
        "-i",
        f"{A}/outro.wav",
        "-i",
        f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
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


videos = [video_tag(0, 0, intro_end, "vert_meiruo")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_baikal"))

labels = []
badges = []
patches = []
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
    if b["badge"]:
        badges.append(
            f'<section id="badge{idx}" class="clip sourceCoverBadge" data-start="{b["start"]}" data-duration="{q(b["end"] - b["start"])}" data-track-index="8">'
            f'<small>难点</small><strong>{b["badge"]}</strong></section>'
        )
    if b.get("patch"):
        patches.append(
            f'<section id="patch{idx}" class="clip sourceCoverPatch" data-start="{b["start"]}" data-duration="{q(b["end"] - b["start"])}" data-track-index="10"></section>'
        )
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:44,opacity:0}},{{y:0,opacity:1,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-26,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')
    if b["badge"]:
        tweens.append(f'tl.fromTo("#badge{idx}",{{opacity:0,y:-12}},{{opacity:1,y:0,duration:.35,ease:"power2.out"}},{q(b["start"]+.2)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "贝加尔湖畔"), ("02", "假如爱有天意"), ("03", "向往"), ("04", "传奇"), ("05", "美若黎明")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06080b;font-family:sans-serif;color:#f5f7f2}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#06080b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.78),rgba(0,0,0,.12) 30%,rgba(0,0,0,.15) 58%,rgba(0,0,0,.84))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.10;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#wash{position:absolute;inset:0;z-index:9;background:radial-gradient(circle at 45% 45%,rgba(140,200,216,.30),rgba(6,8,11,.96) 62%);pointer-events:none;opacity:0}
#cover{position:absolute;inset:0;z-index:5;padding:164px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#8cc8d8}
.eyebrow:before{content:"";width:52px;height:4px;background:#8cc8d8;border-radius:99px}
#cover h1{margin-top:28px;font-size:126px;line-height:1.05;font-weight:950;max-width:900px}
#cover .sub{margin-top:28px;font-size:38px;line-height:1.45;color:#d8ddd5;font-weight:650;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:880px}
.chips span{border:1px solid rgba(140,200,216,.58);color:#dff8ff;background:rgba(5,8,12,.58);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(5,8,12,.84),rgba(5,8,12,.54));border-left:8px solid #8cc8d8}
.fullLabel .rank{font-size:30px;font-weight:900;color:#8cc8d8}
.fullLabel h2{margin-top:14px;font-size:80px;line-height:1.08;font-weight:950}
.fullLabel .tag{margin-top:18px;font-size:40px;line-height:1.28;font-weight:850;color:#d8edf2}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#c3c9c0}
.fullLabel.topRank{border-left-color:#d8b56d}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f1d58c}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(5,8,12,.74);border:1px solid rgba(140,200,216,.58);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#8cc8d8}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(216,181,109,.78)}
.miniLabel.topRank span{color:#f1d58c}
.sourceCoverBadge{position:absolute;z-index:6;top:710px;right:80px;width:330px;min-height:126px;padding:22px 26px;background:rgba(6,8,11,.96);border:2px solid rgba(216,181,109,.72);box-shadow:0 18px 44px rgba(0,0,0,.45)}
.sourceCoverBadge small{display:block;font-size:22px;font-weight:900;color:#8cc8d8}
.sourceCoverBadge strong{display:block;margin-top:8px;font-size:38px;line-height:1.1;color:#f5f7f2}
.sourceCoverPatch{position:absolute;z-index:6;top:875px;right:238px;width:245px;height:92px;background:rgba(6,8,11,.96);border:1px solid rgba(216,181,109,.42);box-shadow:0 14px 34px rgba(0,0,0,.36)}
#outro{position:absolute;z-index:5;inset:0;padding:150px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#8cc8d8}
#outro h2{margin-top:18px;font-size:69px;line-height:1.15;font-weight:950;max-width:900px}
#outro ol{margin-top:44px;list-style:none;display:grid;gap:16px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(5,8,12,.66);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#8cc8d8}
#outro li:first-child span{color:#f1d58c}
#outro li strong{font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.45;color:#d8ddd5;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:96px;text-align:center}
#cta .v{font-size:46px;font-weight:950;color:#f1d58c;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#8cc8d8}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="wash" class="clip" data-start="0" data-duration="{total}" data-track-index="9"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>李健最难的5首歌</h1>'
    '<p class="sub">不是比谁更炸，而是比谁能把轻声、长线条、气息和情绪，稳稳放在同一个音色里。</p></div>'
    '<div class="chips"><span>高位弱声</span><span>长气息</span><span>干净音准</span><span>情绪递进</span><span>空灵流动</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += "\n" + "\n".join(badges)
body += "\n" + "\n".join(patches)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>李健的难，是轻到像没用力，却每一口气都在控制。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期从第五到第一收束：美若黎明、传奇、向往、假如爱有天意、贝加尔湖畔。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

cut_times = list(dict.fromkeys([intro_end] + [b["start"] for b in blocks] + [outro_start]))
wash_tweens = "\n".join(
    f'tl.fromTo("#wash",{{opacity:0.92}},{{opacity:0,duration:.72,ease:"sine.out"}},{q(max(0.0, t-.05))});'
    for t in cut_times
)

js = f"""
tl.fromTo("#cover .eyebrow",{{x:-24,opacity:0}},{{x:0,opacity:1,duration:.55,ease:"power2.out"}},0.35);
tl.fromTo("#cover h1",{{y:52,opacity:0}},{{y:0,opacity:1,duration:.75,ease:"power4.out"}},0.65);
tl.fromTo("#cover .sub",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},1.15);
tl.fromTo("#cover .chips span",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out",stagger:.08}},1.55);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
{wash_tweens}
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(cta_voice+0.35)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "lijian-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
