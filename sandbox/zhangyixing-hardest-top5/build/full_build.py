#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 张艺兴最难的5首歌.

Countdown 5 -> 1 (#1 = 莲 climax，按用户给定难度排名)。选源现实（见 SOURCES.md）：
- 4 首（面纱/梦不落雨林/飞天/莲）为真人官方 MV / 官方练习室，全部 COUPLED（画面+音频同源，mseek 一致，口型同步）。
- 《酒》全网无真人出镜官方内容，仅一支官方概念视觉（张艺兴工作室发布，非静态图，随歌词有光影动效）——
  本曲画面即为该官方视觉本身（非从别处借脸的解耦），已在 SOURCES.md 记录选源现实。
- 因《酒》是倒数第一首出场却无真人，「盘点类封面=第一首出场歌」默认失效：
  片头/片尾改用《莲》同一条连续镜头（古城门+行军，t=11-41s，与 P1 展示段是不同时间点）做首尾呼应，
  保住「封面必须真人」硬约束；倒数环节仍从《酒》正常开始。

Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> render only intro + #5 + outro pilot. HTML_ONLY=1 -> skip audio rebuild.
"""
import contextlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
RAW = ROOT / "raw"
CS = ROOT / "clips_seg"
CS.mkdir(exist_ok=True)

SAMPLE = os.environ.get("SAMPLE") == "1"
HTML_ONLY = os.environ.get("HTML_ONLY") == "1"

LEAD = 0.35
POST = 0.25
DIG = 1.45
BED = 0.16
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.15
OUTRO_TAIL = 2.8
DIGEST_O = 1.05
MASTER_GAIN = 1.03

# intro/outro 床 = 《莲》本曲（与片头片尾同源画面呼应）
INTRO_BED_AUD = "lian"
INTRO_BED_SEEK = 2.0
OUTRO_BED_AUD = "lian"
OUTRO_BED_SEEK = 193.0   # 接续 P1 展示段结尾（160.73+31.61=192.34），音乐自然延续


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


ITEMS = [
    {
        "key": "p5_jiu", "no": "05", "aud": "jiu",
        "name": "《酒》", "plain": "酒", "meta": "出道十周年单曲 · 2022",
        "show": 21.9, "ch_off": 51.38, "mgain": 1.0,
        "tag": "不炸，但松弛感最难拿捏",
        "note": "微醺感里，藏着更细腻的张艺兴",
    },
    {
        "key": "p4_mianshan", "no": "04", "aud": "mianshan",
        "name": "《面纱》", "plain": "面纱", "meta": "电子氛围单曲 · 2022",
        "show": 25.0, "ch_off": 152.27, "mgain": 1.0,
        "tag": "暧昧与神秘，最吃细节",
        "note": "唱实丢性感，唱虚没支撑",
    },
    {
        "key": "p3_menglin", "no": "03", "aud": "menglin",
        "name": "《梦不落雨林》", "plain": "梦不落雨林", "meta": "同名专辑主打曲 · 2018",
        "show": 29.31, "ch_off": 189.41, "mgain": 1.0,
        "tag": "靠groove，不靠飙高音",
        "note": "身体的律动，一秒都不能停",
    },
    {
        "key": "p2_feitian", "no": "02", "aud": "feitian",
        "name": "《飞天》", "plain": "飞天", "meta": "EP《东/EAST》· 2021",
        "show": 32.26, "ch_off": 155.04, "mgain": 1.0,
        "tag": "官方练习室实证的舞台型难度",
        "note": "轻盈与力量，缺一不可",
    },
    {
        "key": "p1_lian", "no": "01", "aud": "lian",
        "name": "《莲》", "plain": "莲", "meta": "唱跳国风单曲 · 2020",
        "show": 31.61, "ch_off": 160.73, "mgain": 1.0,
        "tag": "张艺兴式高难：狠、稳、扛得住",
        "note": "压轴天花板",
    },
]

items = [ITEMS[0]] if SAMPLE else ITEMS

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
    mseek = q(max(0, item["ch_off"] - full_start_local))  # music slice start = same source time as vert clip
    block = {
        **item,
        "clip": f"vert_{item['key']}",
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

# ---- 展示段对齐闸门（硬规则 (C)，违规不出 master）----
sys.path.insert(0, str(ROOT.parents[1]))  # repo root，让 tools 可 import
from tools.video import showcase_align  # noqa: E402
showcase_align.gate(blocks, ROOT / "probe" / "vocal_analysis.json",
                    consts=dict(POST=POST, DIG=DIG),
                    plan_path=ROOT / "probe" / "showcase_plan.json")


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

if not HTML_ONLY:
    run([
        "ffmpeg", "-v", "error", "-i", str(C / "vert_intro.mp4"), "-t", str(intro_end),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / "intro.mp4"), "-y",
    ])
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(INTRO_BED_SEEK), "-i", str(RAW / f"{INTRO_BED_AUD}_aud.wav"),
        "-i", str(A / "intro.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.12,afade=t=in:st=0:d=0.7,afade=t=out:st={q(intro_end-0.8)}:d=0.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ])
segments.append("seg_intro.wav")

for block in blocks:
    seg = CS / f"{block['key']}.mp4"
    if not HTML_ONLY:
        run([
            "ffmpeg", "-v", "error", "-i", str(C / f"vert_{block['key']}.mp4"), "-t", str(block["seg_dur"]),
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
            str(seg), "-y",
        ])
        narr_end_local = q(LEAD + block["voice_dur"])
        env = envelope(narr_end_local, block["full_start_local"])
        gain = block.get("mgain", 1.0)
        out = f"seg_{block['key']}.wav"
        run([
            "ffmpeg", "-v", "error",
            "-ss", str(block["mseek"]), "-i", str(RAW / f"{block['aud']}_aud.wav"),
            "-i", str(A / f"{block['key']}.wav"),
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{block['seg_dur']},volume={gain},volume='{env}':eval=frame[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=level=disabled:limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ])
    segments.append(f"seg_{block['key']}.wav")

outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
if not HTML_ONLY:
    run([
        "ffmpeg", "-v", "error", "-i", str(C / "vert_outro.mp4"), "-t", str(outro_dur),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / "outro.mp4"), "-y",
    ])
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(OUTRO_BED_SEEK), "-i", str(RAW / f"{OUTRO_BED_AUD}_aud.wav"),
        "-i", str(A / "outro.wav"),
        "-i", str(A / "outro_cta.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.18,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ])
segments.append("seg_outro.wav")

if not HTML_ONLY:
    ftrack = ["clips_seg/intro.mp4"] + [f"clips_seg/{b['key']}.mp4" for b in blocks] + ["clips_seg/outro.mp4"]
    (ROOT / "footage_seglist.txt").write_text("".join(f"file '{name}'\n" for name in ftrack), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "footage_seglist.txt",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", str(CS / "footage_track.mp4"), "-y",
    ])

if not HTML_ONLY:
    (ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
        "-af", f"volume={MASTER_GAIN},alimiter=level=disabled:limit=0.97",
        "-ac", "2", "-ar", "48000", "master.wav", "-y",
    ])
    print("master dur:", dur(ROOT / "master.wav"), "planned:", total)


videos = [
    f'<video id="v0" class="clip fv" data-start="0" data-duration="{total}" '
    f'data-track-index="0" src="clips_seg/footage_track.mp4" muted playsinline></video>'
]

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
    e = block["end"]
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(s+.18)});')
    tweens.append(f'tl.fromTo("#{fid} .meta",{{x:-22,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"sine.out"}},{q(s+.34)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:46,opacity:0}},{{y:0,opacity:1,duration:.64,ease:"power3.out"}},{q(s+.5)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power1.out"}},{q(s+.86)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+1.12)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(fs-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(fs)});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(fs+.1)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(e-.35)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{q(e)});')

transition_divs = []
transition_tweens = []
for i, block in enumerate(blocks):
    tid = f"tr{i}"
    ts = q(max(0, block["start"] - 0.15))
    transition_divs.append(
        f'<div id="{tid}" class="clip trans" data-start="{ts}" data-duration="0.9" data-track-index="8"></div>'
    )
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.6,scaleY:.04}},{{opacity:0,scaleY:1,duration:.78,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "酒"),
        ("04", "面纱"),
        ("03", "梦不落雨林"),
        ("02", "飞天"),
        ("01", "莲"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080d;
  font-family:"PingFang SC",system-ui,sans-serif;color:#eef1f6;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07080d}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(7,8,13,.90),rgba(7,8,13,.05) 30%,rgba(7,8,13,.18) 55%,rgba(4,5,10,.95))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.42;background:radial-gradient(42% 26% at 18% 16%,rgba(143,123,255,.42),rgba(143,123,255,0) 65%),radial-gradient(48% 30% at 82% 82%,rgba(110,90,220,.30),rgba(110,90,220,0) 68%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.055;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(238,241,246,.13) 0 1px,rgba(238,241,246,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(180,166,255,0),rgba(180,166,255,.56),rgba(110,90,220,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:120px 76px 116px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(7,8,13,.82),rgba(7,8,13,.10) 30%,rgba(7,8,13,.22) 60%,rgba(4,5,10,.92))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#b6a8ff;letter-spacing:.10em}
.eyebrow:before{content:"";width:58px;height:4px;background:#b6a8ff;border-radius:99px;box-shadow:0 0 18px rgba(182,168,255,.60)}
#cover h1{margin-top:28px;font-family:"Songti SC",serif;font-size:104px;line-height:1.12;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.70)}
#cover h1 b{color:#c7bdff;font-weight:900}
#cover .sub{margin-top:552px;font-size:35px;line-height:1.5;color:#d6dde7;font-weight:600;max-width:920px;text-shadow:0 3px 20px rgba(0,0,0,.8)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(182,168,255,.48);color:#e4ddff;background:rgba(7,8,13,.56);font-size:27px;font-weight:800;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(7,8,13,.91),rgba(26,20,42,.56));border-left:8px solid #8f7bff;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.36)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#b6a8ff;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#a89fc2;letter-spacing:.04em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:82px;line-height:1.12;font-weight:900;color:#eef1f6}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#c7bdff}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#d6dde7}
.fullLabel.topRank{border-left-color:#e8c977;background:linear-gradient(135deg,rgba(18,14,8,.93),rgba(7,8,13,.60))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f0d488}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(7,8,13,.70);border:1.5px solid rgba(182,168,255,.50);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#eef1f6;background:#07080d;border:1px solid rgba(182,168,255,.48);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(232,201,119,.76)}
.miniLabel.topRank span{border-color:rgba(232,201,119,.70)}
#outro{position:absolute;z-index:5;inset:0;padding:110px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(7,8,13,.40),rgba(7,8,13,.90))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#b6a8ff;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:52px;line-height:1.3;font-weight:900;max-width:936px}
#outro ol{margin-top:34px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(7,8,13,.64);border:1px solid rgba(238,241,246,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#eef1f6;background:#07080d;border:1px solid rgba(182,168,255,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(232,201,119,.14);border-color:rgba(232,201,119,.45)}
#outro li:last-child span{border-color:rgba(232,201,119,.65)}
#outro li strong{font-family:"Songti SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:28px;font-size:30px;line-height:1.5;color:#d6dde7;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px;background:rgba(7,8,13,.72);border:1.5px solid rgba(232,201,119,.42);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f0d488;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#b6a8ff;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">唱跳实力派 · 难度盘点</div><h1>张艺兴<br><b>最难</b>的5首歌</h1></div>'
    '<div><p class="sub">唱跳全能，是外界给张艺兴的标签。但他的歌单里，藏着几首连他自己都要全力以赴的作品——说唱、国风、气息、舞台，样样顶到极限。今天倒数盘点，张艺兴最难的五首歌。</p>'
    '<div class="chips" style="margin-top:26px"><span>气息控制</span><span>舞台气场</span><span>说唱咬字</span><span>节奏律动</span><span>情绪细节</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>张艺兴的难，从来不只是唱得多高，而是唱跳说唱舞台全部叠加时，声音还能不能稳得住。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这五首歌，刚好拼出了他作为唱跳歌手最完整的实力版图。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">你最想为哪一首投票？评论区告诉我</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.018,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.25);
tl.fromTo("#glow",{{x:-18,y:0}},{{x:20,y:-14,duration:{total},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.42,ease:"power1.in"}},{q(intro_end-.5)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
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
    "id": "main", "name": "zhangyixing-hardest-top5", "sample": SAMPLE,
    "total": total, "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "aud": b["aud"], "start": b["start"], "narr_start": b["narr_start"],
         "narr_end": b["narr_end"], "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "ch_off": b["ch_off"], "show": b["show"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start, "SAMPLE:", SAMPLE)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"]) for b in blocks])
