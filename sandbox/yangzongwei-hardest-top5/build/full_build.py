#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Yang Zongwei hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 36.0
SHOW_MAP = {
    "p5_yueguoshanqiu": 38.0,
    "p4_liangliang": 33.0,
    "p3_yicijiuhao": 30.0,
    "p2_qishidoumeiyou": 30.0,
    "p1_yangcong": 38.0,
}
LEAD = 0.35
DIG = 1.5
BED = 0.14
VOICE_GAIN = 2.0
MGAIN = {"p5_yueguoshanqiu": 1.04, "p3_yicijiuhao": 1.08, "p1_yangcong": 1.1}
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.8
DIGEST_O = 1.0


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
        "key": "p5_yueguoshanqiu",
        "clip": "vert_yueguoshanqiu",
        "no": "05",
        "name": "《越过山丘》",
        "plain": "越过山丘",
        "tag": "难在把时间唱出重量",
        "note": "阅历感、沧桑感、自我回望",
        "source_start": 126.0,
    },
    {
        "key": "p4_liangliang",
        "clip": "vert_liangliang",
        "no": "04",
        "name": "《凉凉》",
        "plain": "凉凉",
        "tag": "合唱分寸比独唱爆发更难",
        "note": "厚度、收束、仙侠宿命感",
        "source_start": 260.35,
    },
    {
        "key": "p3_yicijiuhao",
        "clip": "vert_yicijiuhao",
        "no": "03",
        "name": "《一次就好》",
        "plain": "一次就好",
        "tag": "温柔长线最怕气息松",
        "note": "长旋律、稳定支撑、克制煽情",
        "source_start": 211.45,
    },
    {
        "key": "p2_qishidoumeiyou",
        "clip": "vert_qishidoumeiyou",
        "no": "02",
        "name": "《其实都没有》",
        "plain": "其实都没有",
        "tag": "空荡感本身要有重量",
        "note": "轻、稳、冷，再慢慢推开",
        "source_start": 120.5,
    },
    {
        "key": "p1_yangcong",
        "clip": "vert_yangcong",
        "no": "01",
        "name": "《洋葱》",
        "plain": "洋葱",
        "tag": "连续递进才是真正难点",
        "note": "气息、声压、情绪一层一层推高",
        "source_start": 177.75,
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
    show = SHOW_MAP.get(item["key"], SHOW)
    end = q(full_start + show)
    b = {**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start, "show": show}
    blocks.append(b)
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
        f"{C}/vert_yueguoshanqiu.mp4",
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
cta_local = q(cta_voice - outro_start)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_yangcong.mp4",
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


videos = [video_tag(0, 0, intro_end, "vert_yueguoshanqiu")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_yangcong"))

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
    tweens.append(f'tl.from("#{fid} .rank",{{x:-28,opacity:0,duration:.45,ease:"power3.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:46,opacity:0,duration:.68,ease:"expo.out"}},{q(b["start"]+.34)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:24,opacity:0,duration:.48,ease:"power2.out"}},{q(b["start"]+.75)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.42,ease:"sine.out"}},{q(b["start"]+1.0)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.42)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-32,opacity:0,duration:.45,ease:"power3.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "洋葱"), ("02", "其实都没有"), ("03", "一次就好"), ("04", "凉凉"), ("05", "越过山丘")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080b;color:#f6efe3;font-family:"Noto Sans SC",sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07080b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:radial-gradient(circle at 20% 18%,rgba(201,155,85,.26),rgba(7,8,11,0) 33%),linear-gradient(to bottom,rgba(4,4,7,.84),rgba(4,4,7,.16) 36%,rgba(4,4,7,.20) 60%,rgba(4,4,7,.86))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.16) 0 1px,rgba(255,255,255,0) 1px 4px);mix-blend-mode:overlay}
.glow{position:absolute;z-index:3;border-radius:999px;filter:blur(28px);opacity:.45;background:#c99b55}
#g1{width:320px;height:320px;right:-90px;top:210px}
#g2{width:260px;height:260px;left:-110px;bottom:360px;background:#7f9aa5;opacity:.30}
#cover{position:absolute;inset:0;z-index:5;padding:156px 74px 148px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#c99b55}
.eyebrow:before{content:"";width:54px;height:4px;background:#c99b55;border-radius:99px}
#cover h1{margin-top:30px;font-family:"Noto Serif SC",serif;font-size:126px;line-height:1.04;font-weight:800;max-width:920px;letter-spacing:.01em}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.45;color:#ded3c5;font-weight:650;max-width:890px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(201,155,85,.58);color:#f1d8aa;background:rgba(8,8,12,.58);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:66px;right:66px;bottom:178px;padding:36px 36px 40px;background:linear-gradient(135deg,rgba(6,7,10,.84),rgba(6,7,10,.54));border-left:8px solid #c99b55;box-shadow:0 24px 70px rgba(0,0,0,.42)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:900;color:#c99b55}
.fullLabel h2{margin-top:14px;font-family:"Noto Serif SC",serif;font-size:82px;line-height:1.08;font-weight:800}
.fullLabel .tag{margin-top:18px;font-size:40px;line-height:1.28;font-weight:850;color:#f0d19a}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#d5c8b9}
.fullLabel.topRank{border-left-color:#b83f46}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff7b83}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(6,7,10,.72);border:1px solid rgba(201,155,85,.58);border-radius:8px;box-shadow:0 18px 50px rgba(0,0,0,.32)}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:950;color:#c99b55}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(184,63,70,.82)}
.miniLabel.topRank span{color:#ff7b83}
#outro{position:absolute;z-index:5;inset:0;padding:142px 74px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#c99b55}
#outro h2{margin-top:18px;font-family:"Noto Serif SC",serif;font-size:70px;line-height:1.15;font-weight:800;max-width:900px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(6,7,10,.64);border:1px solid rgba(255,255,255,.13);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:34px;font-weight:950;color:#c99b55}
#outro li:first-child span{color:#ff7b83}
#outro li strong{font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:32px;font-size:31px;line-height:1.45;color:#d9d0c5;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:92px;text-align:center}
#cta .v{font-size:46px;font-weight:950;color:#ff7b83;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#c99b55;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="g1" class="clip glow" data-start="0" data-duration="{total}" data-track-index="8"></div>'
body += f'\n<div id="g2" class="clip glow" data-start="0" data-duration="{total}" data-track-index="9"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.15" data-duration="{q(intro_end-.3)}" data-track-index="2">'
    '<div><div class="eyebrow">声线难度盘点</div><h1>杨宗纬最难的5首歌</h1>'
    '<p class="sub">不是只看高音，而是看气息、声压、咬字和情绪，能不能在最脆弱的地方同时稳住。</p></div>'
    '<div class="chips"><span>气息长线</span><span>情绪推进</span><span>声压控制</span><span>克制爆发</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>最难的不是唱哭，而是把脆弱唱稳。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期从第五到第一收束：越过山丘、凉凉、一次就好、其实都没有、洋葱。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.from("#cover .eyebrow",{{x:-26,opacity:0,duration:.55,ease:"power3.out"}},0.28);
tl.from("#cover h1",{{y:54,opacity:0,duration:.78,ease:"expo.out"}},0.55);
tl.from("#cover .sub",{{y:28,opacity:0,duration:.56,ease:"power2.out"}},1.12);
tl.from("#cover .chips span",{{y:22,opacity:0,duration:.45,ease:"sine.out",stagger:.08}},1.55);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
tl.to("#g1",{{scale:1.18,x:-50,y:38,duration:{q(total/2)},ease:"sine.inOut"}},0);
tl.to("#g2",{{scale:1.14,x:42,y:-60,duration:{q(total/2)},ease:"sine.inOut"}},0);
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power3.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:42,opacity:0,duration:.68,ease:"expo.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"sine.out"}},{q(outro_start+2.0)});
tl.from("#cta .v",{{y:26,opacity:0,duration:.55,ease:"power3.out"}},{q(cta_voice)});
tl.from("#cta .f",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(cta_voice+0.35)});
tl.to("#cta",{{opacity:0,duration:.5,ease:"power1.in"}},{q(total-.75)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "yangzongwei-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
(ROOT / "timeline.json").write_text(
    json.dumps({"total": total, "intro_end": intro_end, "outro_start": outro_start, "cta_voice": cta_voice, "blocks": blocks}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])

