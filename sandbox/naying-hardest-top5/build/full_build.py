#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Na Ying hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 38.0
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {"p3_baitian": 1.12, "p1_zhengfu": 1.1}
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
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
        "key": "p5_buguan",
        "clip": "vert_buguan",
        "no": "05",
        "name": "《不管有多苦》",
        "plain": "不管有多苦",
        "tag": "强情绪和强机能同时顶住",
        "note": "中高区支撑、气息耐力、持续输出",
        "mask": True,
    },
    {
        "key": "p4_chumai",
        "clip": "vert_chumai",
        "no": "04",
        "name": "《出卖》",
        "plain": "出卖",
        "tag": "痛感不能轻，也不能硬吼",
        "note": "背叛感、音准、收束能力都要稳",
        "mask": False,
    },
    {
        "key": "p3_baitian",
        "clip": "vert_baitian",
        "no": "03",
        "name": "《白天不懂夜的黑》",
        "plain": "白天不懂夜的黑",
        "tag": "大开大合的高位强声",
        "note": "厚度、亮度、咬字和音准同时在线",
        "mask": True,
    },
    {
        "key": "p2_mo",
        "clip": "vert_mo",
        "no": "02",
        "name": "《默》",
        "plain": "默",
        "tag": "克制一路推到爆发",
        "note": "低压状态、高位推进、长气息",
        "mask": False,
    },
    {
        "key": "p1_zhengfu",
        "clip": "vert_zhengfu",
        "no": "01",
        "name": "《征服》",
        "plain": "征服",
        "tag": "那英声乐难度代表作",
        "note": "高位强声、沙哑亮度、情绪爆发",
        "mask": True,
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
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_buguan.mp4",
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
        f"{C}/vert_zhengfu.mp4",
        "-i",
        f"{A}/outro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.2}:d=1.2[music];"
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


videos = [video_tag(0, 0, intro_end, "vert_buguan")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_zhengfu"))

labels = []
masks = []
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
    if b["mask"]:
        masks.append(
            f'<div id="mask{idx}" class="clip lyricMask" data-start="{b["start"]}" '
            f'data-duration="{q(b["end"] - b["start"])}" data-track-index="8"></div>'
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
    for n, name in [("01", "征服"), ("02", "默"), ("03", "白天不懂夜的黑"), ("04", "出卖"), ("05", "不管有多苦")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070a;font-family:sans-serif;color:#f8f3ec}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.76),rgba(0,0,0,.12) 32%,rgba(0,0,0,.18) 58%,rgba(0,0,0,.82))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.15) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
.lyricMask{position:absolute;left:0;right:0;top:930px;height:500px;z-index:3;background:rgba(8,7,10,.99);box-shadow:0 -18px 54px rgba(0,0,0,.80),0 18px 54px rgba(0,0,0,.70)}
#cover{position:absolute;inset:0;z-index:5;padding:164px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#d6b16a}
.eyebrow:before{content:"";width:52px;height:4px;background:#d6b16a;border-radius:99px}
#cover h1{margin-top:28px;font-size:132px;line-height:1.03;font-weight:950;max-width:900px;text-wrap:balance}
#cover .sub{margin-top:28px;font-size:38px;line-height:1.45;color:#d7cfc2;font-weight:650;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:880px}
.chips span{border:1px solid rgba(214,177,106,.55);color:#f4dcae;background:rgba(10,10,14,.52);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(5,5,8,.82),rgba(5,5,8,.50));border-left:8px solid #d6b16a}
.fullLabel .rank{font-size:30px;font-weight:900;color:#d6b16a}
.fullLabel h2{margin-top:14px;font-size:84px;line-height:1.06;font-weight:950}
.fullLabel .tag{margin-top:18px;font-size:41px;line-height:1.28;font-weight:850;color:#f0d19a}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#cec4b8}
.fullLabel.topRank{border-left-color:#c7333f}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff727d}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(5,5,8,.70);border:1px solid rgba(214,177,106,.58);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#d6b16a}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(199,51,63,.78)}
.miniLabel.topRank span{color:#ff727d}
#outro{position:absolute;z-index:5;inset:0;padding:150px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#d6b16a}
#outro h2{margin-top:18px;font-size:72px;line-height:1.13;font-weight:950;max-width:900px}
#outro ol{margin-top:44px;list-style:none;display:grid;gap:16px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(5,5,8,.62);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#d6b16a}
#outro li:first-child span{color:#ff727d}
#outro li strong{font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.45;color:#d7cfc2;font-weight:650}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += "\n" + "\n".join(masks)
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>那英最难的5首歌</h1>'
    '<p class="sub">不是只比高音，而是看厚度、穿透力、气息、咬字和情绪爆发，能不能在高压区同时稳住。</p></div>'
    '<div class="chips"><span>高位强声</span><span>沙哑亮度</span><span>情绪爆发</span><span>长气息</span><span>持续输出</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>那英的难，是力量、沙哑和亮度在同一个点上稳住。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期按难度从第五到第一收束：不管有多苦、出卖、白天不懂夜的黑、默、征服。</p></section>'
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "naying-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
