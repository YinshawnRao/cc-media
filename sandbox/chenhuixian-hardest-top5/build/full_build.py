#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 陈慧娴最难的5首歌.

Countdown 5 -> 1 (#1 = 月亮, the climax). COUPLED audio: every song's footage AND music
come from the SAME source window (official MV / clean TV perf), so the showcase chorus
lip-syncs. Per segment both video (clips_seg/<key>.mp4) and music (raw/<key>_aud.wav)
are sliced from `mseek` so the chorus (ch_off, vert-local source time) lands at the
full-volume showcase start.

事实口径（web 核实）：千千阙歌/夜机=1989《永远是你的朋友》(宝丽金,告别专辑)；
月亮/飘雪/归来吧=1992《归来吧》(美国念书期录制)。选源见 SOURCES.md。
固定结尾 CTA 永远最后一句（防双 CTA：outro 不带投票问句）。

Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> render intro + #5 + outro pilot. HTML_ONLY=1 -> skip audio rebuild.
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
sys.path.insert(0, str(ROOT.parents[1]))  # repo root -> import tools
from tools.video import showcase_align  # noqa: E402

SAMPLE = os.environ.get("SAMPLE") == "1"
HTML_ONLY = os.environ.get("HTML_ONLY") == "1"
AUDIO_ONLY = os.environ.get("AUDIO_ONLY") == "1"  # rebuild audio/master only, reuse cached footage_track
DO_FOOTAGE = not HTML_ONLY and not AUDIO_ONLY

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

# intro/outro music bed = 月亮 (#1 climax, studio audio) — soft intro instr, chorus for outro
INTRO_BED_AUD = "yueliang"
INTRO_BED_SEEK = 2.0
OUTRO_BED_AUD = "yueliang"
OUTRO_BED_SEEK = 106.0


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


# reveal order 5 -> 1. ch_off = chorus onset in vert-clip local (source) time (== showcase
# full-music start); show = showcase seconds. Derived from vocal_analysis + frame checks.
ITEMS = [
    {
        "key": "guilai", "no": "05",
        "name": "《归来吧》", "plain": "归来吧", "meta": "归来吧 · 1992",
        "show": 32.0, "ch_off": 106.0, "mgain": 1.0,
        "tag": "大歌要唱得开阔，又不能喊口号",
        "note": "美国念书期录的专辑同名曲，最考验声音的端正和分寸",
    },
    {
        "key": "yeji", "no": "04",
        "name": "《夜机》", "plain": "夜机", "meta": "永远是你的朋友 · 1989",
        # 末段副歌(歌词逐行推进确认真唱)：今天起的每晚→…→原諒今宵我告別了。
        # 原172-203窗撞上176-196的萨克斯间奏(vocal_segments对该源误报)→用户耳验无人声，已改。
        "show": 34.0, "ch_off": 204.0, "mgain": 1.3,  # final chorus was -17.6dB -> lift to ~-15.5
        "tag": "夜航的孤独，副歌才慢慢打开",
        "note": "中低音叙事，粤语咬字和换气的气口都得稳",
    },
    {
        "key": "piaoxue", "no": "03",
        "name": "《飘雪》", "plain": "飘雪", "meta": "归来吧 · 1992",
        "show": 24.0, "ch_off": 85.0, "mgain": 1.06,
        "tag": "唱的不是伤心，是雪落下来的冷",
        "note": "尾音稍一脏，那份雪夜里的孤清就没了",
    },
    {
        "key": "qianqian", "no": "02",
        "name": "《千千阙歌》", "plain": "千千阙歌", "meta": "永远是你的朋友 · 1989",
        "show": 29.5, "ch_off": 264.0, "mgain": 1.22,  # live finale was -17.4dB -> lift to ~-15.5
        "tag": "离别，但不狼狈的那份体面",
        "note": "难的不是高音，是一路推到万人合唱的气息耐力",
    },
    {
        "key": "yueliang", "no": "01",
        "name": "《月亮》", "plain": "月亮", "meta": "归来吧 · 1992",
        "show": 26.0, "ch_off": 234.0, "mgain": 1.5,  # delicate weak-voice chorus was -18.8dB -> lift to ~-16
        "tag": "越轻，越难",
        "note": "长线条、弱声、高位稳定，一重就没了月光感",
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
    mseek = q(max(0, item["ch_off"] - full_start_local))  # slice both video & music from here
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

# ---- 🔒 showcase alignment gate (FAIL -> no master) ----
showcase_align.gate(blocks, ROOT / "probe" / "vocal_analysis.json",
                    consts=dict(POST=POST, DIG=DIG, LEAD=LEAD),
                    plan_path=ROOT / "build" / "showcase_plan.json")

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

if DO_FOOTAGE:
    # ---- intro: footage video-only slice ----
    run([
        "ffmpeg", "-v", "error", "-i", str(C / "vert_intro.mp4"), "-t", str(intro_end),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / "intro.mp4"), "-y",
    ])
if not HTML_ONLY:
    # ---- intro audio: bed (月亮 soft instr) + voice ----
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
    if DO_FOOTAGE:
        # COUPLED — VIDEO: slice footage from mseek (so chorus lands at showcase start), video-only
        run([
            "ffmpeg", "-v", "error", "-ss", str(block["mseek"]), "-i", str(C / f"vert_{block['key']}.mp4"),
            "-t", str(block["seg_dur"]),
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
            str(seg), "-y",
        ])
    if not HTML_ONLY:
        # COUPLED — MUSIC: same source's audio sliced from same mseek -> lip-sync preserved
        narr_end_local = q(LEAD + block["voice_dur"])
        env = envelope(narr_end_local, block["full_start_local"])
        gain = block.get("mgain", 1.0)
        out = f"seg_{block['key']}.wav"
        run([
            "ffmpeg", "-v", "error",
            "-ss", str(block["mseek"]), "-i", str(RAW / f"{block['key']}_aud.wav"),
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
if DO_FOOTAGE:
    run([
        "ffmpeg", "-v", "error", "-i", str(C / "vert_outro.mp4"), "-t", str(outro_dur),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / "outro.mp4"), "-y",
    ])
if not HTML_ONLY:
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

if DO_FOOTAGE:
    # 单条 footage_track（硬规则：长片多 <video> 会让 HF 帧0 协议超时；拼成 1 条只挂 1 个 video）
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


# 单条 footage_track（轻量模式，只挂 1 个 <video>，避免 HF 帧0 协议超时）
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
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.54,scaleY:.04}},{{opacity:0,scaleY:1,duration:.78,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "归来吧"),
        ("04", "夜机"),
        ("03", "飘雪"),
        ("02", "千千阙歌"),
        ("01", "月亮"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#080a0f;
  font-family:"PingFang SC",system-ui,sans-serif;color:#eef1f6;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#080a0f}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,10,15,.90),rgba(8,10,15,.05) 30%,rgba(8,10,15,.18) 55%,rgba(5,6,11,.95))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.40;background:radial-gradient(42% 26% at 18% 16%,rgba(150,170,224,.42),rgba(150,170,224,0) 65%),radial-gradient(48% 30% at 82% 82%,rgba(120,140,200,.28),rgba(120,140,200,0) 68%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.055;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(238,241,246,.13) 0 1px,rgba(238,241,246,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(163,184,224,0),rgba(163,184,224,.52),rgba(120,140,200,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:120px 76px 116px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(8,10,15,.82),rgba(8,10,15,.10) 30%,rgba(8,10,15,.22) 60%,rgba(5,6,11,.92))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#a8c2ea;letter-spacing:.10em}
.eyebrow:before{content:"";width:58px;height:4px;background:#a8c2ea;border-radius:99px;box-shadow:0 0 18px rgba(168,194,234,.60)}
#cover h1{margin-top:28px;font-family:"Songti SC",serif;font-size:104px;line-height:1.1;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.70)}
#cover h1 b{color:#b9d2f2;font-weight:900}
#cover .sub{margin-top:566px;font-size:35px;line-height:1.5;color:#d6dde7;font-weight:600;max-width:920px;text-shadow:0 3px 20px rgba(0,0,0,.8)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(168,194,234,.48);color:#dfeaf6;background:rgba(8,10,15,.56);font-size:27px;font-weight:800;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(8,10,15,.91),rgba(22,28,42,.56));border-left:8px solid #6f8fc4;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.36)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#a8c2ea;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#9fb0c2;letter-spacing:.06em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:80px;line-height:1.12;font-weight:900;color:#eef1f6}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#b9d2f2}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#d6dde7}
.fullLabel.topRank{border-left-color:#e8c977;background:linear-gradient(135deg,rgba(18,14,8,.93),rgba(8,10,15,.60))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f0d488}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(8,10,15,.70);border:1.5px solid rgba(168,194,234,.50);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#eef1f6;background:#080a0f;border:1px solid rgba(168,194,234,.48);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(232,201,119,.76)}
.miniLabel.topRank span{border-color:rgba(232,201,119,.70)}
#outro{position:absolute;z-index:5;inset:0;padding:110px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(8,10,15,.40),rgba(8,10,15,.90))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#a8c2ea;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:54px;line-height:1.3;font-weight:900;max-width:936px}
#outro ol{margin-top:34px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(8,10,15,.64);border:1px solid rgba(238,241,246,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#eef1f6;background:#080a0f;border:1px solid rgba(168,194,234,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(232,201,119,.14);border-color:rgba(232,201,119,.45)}
#outro li:last-child span{border-color:rgba(232,201,119,.65)}
#outro li strong{font-family:"Songti SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:28px;font-size:30px;line-height:1.5;color:#d6dde7;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px;background:rgba(8,10,15,.72);border:1.5px solid rgba(232,201,119,.42);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f0d488;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#a8c2ea;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<img id="coverhero" class="clip" data-start="0" data-duration="{q(intro_end-.08)}" data-track-index="11" '
    f'src="cover_hero.png" style="position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:4" />'
)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">港乐经典 · 越轻越难唱</div><h1>陈慧娴<br><b>最难</b>的5首歌</h1></div>'
    '<div><p class="sub">不是飙高音的那种难，而是又轻、又稳、又体面——这五首，最能听出陈慧娴的控制力。</p>'
    '<div class="chips" style="margin-top:26px"><span>弱声控制</span><span>气息耐力</span><span>粤语咬字</span><span>情绪分寸</span><span>越轻越难</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>陈慧娴最难的歌，几乎都不靠飙高音取胜，而是赢在那种又轻、又稳、又体面的控制力。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">把最汹涌的情绪，唱得云淡风轻——这，就是陈慧娴。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.018,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.25);
tl.fromTo("#glow",{{x:-18,y:0}},{{x:20,y:-14,duration:{total},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.42,ease:"power1.in"}},{q(intro_end-.5)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
tl.to("#coverhero",{{opacity:0,duration:.42,ease:"power1.in"}},{q(intro_end-.5)});
tl.set("#coverhero",{{opacity:0}},{q(intro_end)});
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
    "id": "main", "name": "chenhuixian-hardest-top5", "sample": SAMPLE,
    "total": total, "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "start": b["start"], "narr_start": b["narr_start"],
         "narr_end": b["narr_end"], "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "ch_off": b["ch_off"], "show": b["show"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start, "SAMPLE:", SAMPLE)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"]) for b in blocks])
