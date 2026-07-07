#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 张宇最被低估的5首歌."""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
CS = ROOT / "clips_seg"
CS.mkdir(exist_ok=True)

REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO))
from tools.video import showcase_align  # noqa: E402

LEAD = 0.35
POST = 0.25
DIG = 1.45
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.15
OUTRO_TAIL = 2.8
DIGEST_O = 1.05
MASTER_GAIN = 1.04

OUTRO_SRC = "vert_yuanhuang"
OUTRO_SEEK = 221.12


def dur(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value: float) -> float:
    return round(float(value), 3)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


items = [
    {
        "key": "p5_shuogushi", "clip": "vert_shuogushi", "no": "05",
        "name": "《说故事》", "plain": "说故事", "meta": "《单恋》 · 1995",
        "show": 33.65, "ch_off": 85.34,
        "tag": "早期叙事感，慢热但有后劲",
        "note": "像坐下来讲一段关系，最后才发现最难受的是自己",
    },
    {
        "key": "p4_xinjing", "clip": "vert_xinjing", "no": "04",
        "name": "《心井》", "plain": "心井", "meta": "《消息》 · 1996",
        "show": 38.92, "ch_off": 153.35,
        "tag": "内收、阴影、深处的回声",
        "note": "不靠爆发，靠沙哑和空洞感慢慢往下沉",
    },
    {
        "key": "p3_qianjin", "clip": "vert_qianjin", "no": "03",
        "name": "《千金难买》", "plain": "千金难买", "meta": "《整个八月》 · 1997",
        "show": 29.30, "ch_off": 103.85,
        "tag": "后悔写得很沉，却不廉价",
        "note": "有些东西再珍贵，也不是用代价就能换回来",
    },
    {
        "key": "p2_shaogeren", "clip": "vert_shaogeren", "no": "02",
        "name": "《不过少个人来爱》", "plain": "不过少个人来爱", "meta": "《整个八月》 · 1997",
        "show": 33.54, "ch_off": 155.02,
        "tag": "故作轻松，才最像成年人失恋",
        "note": "越像在硬撑，情绪越往下沉",
    },
    {
        "key": "p1_yuanhuang", "clip": "vert_yuanhuang", "no": "01",
        "name": "《圆谎》", "plain": "圆谎", "meta": "《消息》 · 1996",
        "show": 25.05, "ch_off": 221.12, "bed": 0.04,
        "tag": "明知有裂缝，还要把谎说圆",
        "note": "十一郎的狠词，张宇把自欺欺人的痛唱得很真",
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
    full_start = q(narr_end + POST + DIG)
    end = q(full_start + item["show"])
    full_start_local = q(full_start - t)
    mseek = q(max(0, item["ch_off"] - full_start_local))
    block = {
        **item,
        "start": q(t), "end": end,
        "narr_start": narr_start, "narr_end": narr_end,
        "full_start": full_start, "full_start_local": full_start_local,
        "mseek": mseek, "seg_dur": q(end - t),
    }
    blocks.append(block)
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)

first = blocks[0]
intro_src_name = first["clip"]
intro_seek = q(max(0, first["mseek"] - intro_end))
first["mseek"] = q(intro_seek + intro_end)
first["ch_off"] = q(first["mseek"] + first["full_start_local"])

showcase_align.gate(
    blocks,
    ROOT / "probe" / "vocal_analysis.json",
    consts={"POST": POST, "DIG": DIG},
    plan_path=ROOT / "probe" / "showcase_plan.json",
)


def envelope(narr_end_local: float, full_start_local: float, bed: float = BED) -> str:
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({bed}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{bed}"
        f"+(between(t,{swell},{full_start_local}))*({bed}+{1.0-bed}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

intro_src = C / f"{intro_src_name}.mp4"
run([
    "ffmpeg", "-v", "error", "-ss", str(intro_seek), "-i", str(intro_src), "-t", str(intro_end),
    "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
    "-an", str(CS / "intro.mp4"), "-y",
])
run([
    "ffmpeg", "-v", "error",
    "-ss", str(intro_seek), "-i", str(intro_src),
    "-i", str(A / "intro.wav"),
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.12,afade=t=in:st=0:d=0.7,afade=t=out:st={q(intro_end-0.8)}:d=0.8[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

for block in blocks:
    src = C / f"{block['clip']}.mp4"
    seg = CS / f"{block['key']}.mp4"
    run([
        "ffmpeg", "-v", "error", "-ss", str(block["mseek"]), "-i", str(src), "-t", str(block["seg_dur"]),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-c:a", "aac", "-b:a", "192k", str(seg), "-y",
    ])
    narr_end_local = q(LEAD + block["voice_dur"])
    env = envelope(narr_end_local, block["full_start_local"], block.get("bed", BED))
    out = f"seg_{block['key']}.wav"
    run([
        "ffmpeg", "-v", "error",
        "-i", str(seg),
        "-i", str(A / f"{block['key']}.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{block['seg_dur']},volume='{env}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
outro_src = C / f"{OUTRO_SRC}.mp4"
run([
    "ffmpeg", "-v", "error", "-ss", str(OUTRO_SEEK), "-i", str(outro_src), "-t", str(outro_dur),
    "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
    "-an", str(CS / "outro.mp4"), "-y",
])
run([
    "ffmpeg", "-v", "error",
    "-ss", str(OUTRO_SEEK), "-i", str(outro_src),
    "-i", str(A / "outro.wav"),
    "-i", str(A / "outro_cta.wav"),
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.16,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run([
    "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
    "-af", f"volume={MASTER_GAIN},alimiter=limit=0.97",
    "-ac", "2", "-ar", "48000", "master.wav", "-y",
])
master_duration = dur(ROOT / "master.wav")
print("master dur:", master_duration, "planned:", total)


def video_tag(idx: int, start: float, duration: float, src: str) -> str:
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="{src}" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, "clips_seg/intro.mp4")]
for idx, block in enumerate(blocks, start=1):
    videos.append(video_tag(idx, block["start"], block["seg_dur"], f"clips_seg/{block['key']}.mp4"))
videos.append(video_tag(len(videos), outro_start, outro_dur, "clips_seg/outro.mp4"))

labels = []
tweens = []
for idx, block in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(block["full_start"] - block["start"])
    mdur = q(block["end"] - block["full_start"])
    top = " topRank" if block["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{top}" data-start="{block["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {block["no"]} 名</div><div class="meta">{block["meta"]}</div><h2>{block["name"]}</h2>'
        f'<p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{top}" data-start="{block["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{block["no"]}</span><strong>{block["plain"]}</strong></section>'
    )
    s = block["start"]
    fs = block["full_start"]
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(s+.18)});')
    tweens.append(f'tl.fromTo("#{fid} .meta",{{x:-22,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"sine.out"}},{q(s+.34)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:48,opacity:0}},{{y:0,opacity:1,duration:.66,ease:"power3.out"}},{q(s+.52)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"expo.out"}},{q(s+.88)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{x:18,opacity:0}},{{x:0,opacity:1,duration:.44,ease:"power1.out"}},{q(s+1.12)});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(fs+.1)});')

transition_divs = []
transition_tweens = []
for i, block in enumerate(blocks):
    tid = f"tr{i}"
    ts = q(max(0, block["start"] - 0.12))
    transition_divs.append(
        f'<div id="{tid}" class="clip trans" data-start="{ts}" data-duration="0.84" data-track-index="8"></div>'
    )
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.64,scaleY:.035}},{{opacity:0,scaleY:1,duration:.74,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "说故事"),
        ("04", "心井"),
        ("03", "千金难买"),
        ("02", "不过少个人来爱"),
        ("01", "圆谎"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#09090a;
  font-family:"PingFang SC",system-ui,sans-serif;color:#f4efe6;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#09090a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(9,9,10,.92),rgba(9,9,10,.18) 31%,rgba(9,9,10,.18) 55%,rgba(9,9,10,.94))}
#wash{position:absolute;inset:0;z-index:1;opacity:.38;background:linear-gradient(135deg,rgba(166,38,31,.34),rgba(10,86,92,.24) 48%,rgba(183,145,76,.20))}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.08;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(244,239,230,.13) 0 1px,rgba(244,239,230,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(166,38,31,0),rgba(166,38,31,.58),rgba(18,129,138,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;opacity:0;padding:126px 72px 126px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(9,9,10,.84),rgba(9,9,10,.18) 33%,rgba(9,9,10,.24) 58%,rgba(9,9,10,.94))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#56c5c0;letter-spacing:.12em}
.eyebrow:before{content:"";width:58px;height:4px;background:#b7914c;border-radius:99px;box-shadow:0 0 18px rgba(183,145,76,.62)}
#cover h1{margin-top:30px;font-family:"Songti SC",serif;font-size:112px;line-height:1.08;font-weight:900;max-width:944px;text-shadow:0 6px 44px rgba(0,0,0,.68)}
#cover h1 b{color:#d74e43;font-weight:900}
#cover .sub{margin-top:32px;font-size:36px;line-height:1.52;color:#dfd4c5;font-weight:650;max-width:920px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(183,145,76,.56);color:#f4efe6;background:rgba(9,9,10,.62);font-size:27px;font-weight:850;padding:12px 18px;border-radius:7px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:164px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(9,9,10,.92),rgba(32,28,24,.64));border-left:8px solid #a6261f;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.40)}
.fullLabel .rank{font-family:"Menlo","Monaco",monospace;font-size:31px;font-weight:900;color:#56c5c0;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:27px;font-weight:750;color:#c4b7a4;letter-spacing:.05em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:76px;line-height:1.12;font-weight:900;color:#f4efe6}
.fullLabel .tag{margin-top:19px;font-size:38px;line-height:1.28;font-weight:900;color:#e06355}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:650;color:#dfd4c5}
.fullLabel.topRank{border-left-color:#56c5c0;background:linear-gradient(135deg,rgba(12,20,20,.94),rgba(9,9,10,.64))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#66d8d1}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(9,9,10,.72);border:1.5px solid rgba(86,197,192,.58);border-radius:7px}
.miniLabel span{font-family:"Menlo","Monaco",monospace;font-size:44px;font-weight:900;color:#f4efe6;background:#09090a;border:1px solid rgba(183,145,76,.58);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:38px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(224,99,85,.76)}
.miniLabel.topRank span{border-color:rgba(224,99,85,.70)}
#outro{position:absolute;z-index:5;inset:0;padding:112px 72px 152px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(9,9,10,.36),rgba(9,9,10,.90))}
#outro .small{font-family:"Menlo","Monaco",monospace;font-size:31px;font-weight:900;color:#56c5c0;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:55px;line-height:1.28;font-weight:900;max-width:932px}
#outro ol{margin-top:38px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(9,9,10,.66);border:1px solid rgba(244,239,230,.14);border-radius:8px}
#outro li span{font-family:"Menlo","Monaco",monospace;font-size:32px;font-weight:900;color:#f4efe6;background:#09090a;border:1px solid rgba(183,145,76,.56);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(166,38,31,.20);border-color:rgba(224,99,85,.50)}
#outro li:last-child span{border-color:rgba(224,99,85,.72)}
#outro li strong{font-family:"Songti SC",serif;font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:30px;font-size:30px;line-height:1.5;color:#dfd4c5;font-weight:650}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:90px;text-align:center;padding:20px;background:rgba(9,9,10,.76);border:1.5px solid rgba(224,99,85,.52);border-radius:8px}
#cta .v{font-size:42px;font-weight:900;color:#e06355;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#56c5c0;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="wash" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 十一郎式苦情</div><h1>张宇<br><b>最被低估</b>的5首歌</h1>'
    '<p class="sub">大热歌之外，这五首更像老粉私藏：叙事、暗涌、后悔、硬撑和自欺欺人的痛。</p></div>'
    '<div class="chips"><span>老派 MV</span><span>慢热遗珠</span><span>内收苦情</span><span>沙哑叙事</span><span>从第5到第1</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>张宇最被低估的，不只是几首遗珠，而是他和十一郎写过更沉、更拧、更耐听的爱情。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">真正有后劲的歌，常常不是第一耳最大的那首。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{master_duration}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

cover_exit_start = q(intro_end - 0.5)
cover_exit_end = q(cover_exit_start + 0.42)

js = f"""
tl.set("#cover",{{opacity:0}},0);
tl.fromTo("#cover",{{opacity:0}},{{opacity:1,duration:.5,ease:"power2.out"}},0.12);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.016,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.25);
tl.fromTo("#wash",{{opacity:.34}},{{opacity:.46,duration:{total},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.42,ease:"power1.in"}},{cover_exit_start});
tl.set("#cover",{{opacity:0}},{cover_exit_end});
{chr(10).join(transition_tweens)}
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.18)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(outro_start+2.18)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power1.out"}},{q(cta_voice+.35)});
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
(ROOT / "meta.json").write_text(json.dumps({
    "id": "main", "name": "zhangyu-underrated-top5",
    "total": total, "master_duration": master_duration, "intro_end": intro_end, "intro_seek": intro_seek,
    "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "start": b["start"], "narr_start": b["narr_start"],
         "narr_end": b["narr_end"], "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "ch_off": b["ch_off"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], b["mseek"]) for b in blocks])
