#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML — 伍佰给女歌手写的歌 TOP10.

倒数 10->1。展示段默认=官方 MV（footage 与音频同源，口型同步, mode="sync"）；
个别 MV 无歌手演唱画面/只有 Live 的，用 footage + 解耦录音室音频(mode="decouple")。
封面/片头/片尾主角 = 词曲作者伍佰本人（多歌手盘点封面放幕后创作者）。
最终音频以本脚本 master.wav 后期 mux 为准（HyperFrames 会压平动态）。
"""
import contextlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

HTML_ONLY = bool(os.environ.get("HTML_ONLY"))    # 只重生成 index.html，跳过 footage/audio 重切
AUDIO_ONLY = bool(os.environ.get("AUDIO_ONLY"))  # 只重建 master.wav（跳过 footage 重切）

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
RAW = ROOT / "raw"
CLIPS = ROOT / "clips"
CS = ROOT / "clips_seg"
CS.mkdir(exist_ok=True)

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
ONSET_LEAD = 2.0  # 副歌入声落在旁白结束前 2s

TITLE = "伍佰给女歌手写的歌 TOP10"
SLUG = "wubai-female-singers-top10"

# 片头/片尾底片 = 伍佰本人镜头（复用含伍佰的现场源不同窗，封面首帧=伍佰正脸）
INTRO_CLIP = "vert_p8"    # 杨乃文真世界巡演 Live：@197.5 伍佰红光脸部特写
INTRO_FSEEK = 197.5
OUTRO_CLIP = "vert_p3"    # 莫文蔚真世界巡演 Live：@34 伍佰红吉他经典像
OUTRO_FSEEK = 34.0


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def arun(cmd):
    if not HTML_ONLY:
        subprocess.run(cmd, cwd=ROOT, check=True)


# 倒数顺序 10 -> 1（列表即展示先后）。
#   mode "sync"     : footage+音频同源(官方MV)；fseek 自动 = aud_start，音频读 clips/vert_<key>.mp4
#   mode "decouple" : footage(Live等) + 解耦音频 RAW/<aud>.mp3；需手填 fseek
#   ch_off : 副歌人声入点（在 clips/vert_<key>.mp4 时间轴；sync 与 footage 同轴）
#   show   : 展示段时长（≥~25s，落在连唱副歌，结尾不切半句）
items = [
    {"key": "p10", "no": "10", "singer": "黄小琥", "song": "突然的自我",
     "meta": "2004 · 专辑《The Voice 3》 · 伍佰 词曲", "mode": "decouple", "aud": "au_p10", "fseek": 17.7,
     "ch_off": 132.4, "show": 26.0,
     "tag": "潇洒里，藏着过来人的认命", "note": "大众更熟伍佰原版，这次换黄小琥的沧桑嗓"},
    {"key": "p9", "no": "09", "singer": "郁可唯", "song": "你不要我了吗",
     "meta": "2012 · 专辑《微加幸福》 · 伍佰 词曲", "mode": "sync",
     "ch_off": 140.95, "show": 32.0,
     "tag": "最不敢问的那句话，成了歌名", "note": "伍佰难得的一道柔软伤口"},
    {"key": "p8", "no": "08", "singer": "杨乃文", "song": "一个人",
     "meta": "1997 · 专辑《One》 · 伍佰 作词", "mode": "sync",
     "ch_off": 156.32, "show": 19.0,
     "tag": "又冷又硬，和伍佰天生一对", "note": "曲 林暐哲／词 伍佰，二人对唱"},
    {"key": "p7", "no": "07", "singer": "刘若英", "song": "最初的地方",
     "meta": "1998 · 专辑《很爱很爱你》 · 伍佰 作曲", "mode": "decouple", "aud": "au_p7", "fseek": 144.3,
     "ch_off": 227.69, "show": 17.5,
     "tag": "民谣摇滚里的一点率性", "note": "代表作太多，这首常被盖过去"},
    {"key": "p6", "no": "06", "singer": "万芳", "song": "夜照亮了夜",
     "meta": "伍佰 作曲（词 王中言）", "mode": "decouple", "aud": "au_p6", "fseek": 35.7,
     "ch_off": 43.82, "show": 25.5,
     "tag": "一盏暗处的灯，不刺眼", "note": "不爆发，却把整个夜慢慢照亮"},
    {"key": "p5", "no": "05", "singer": "那英", "song": "我不是天使",
     "meta": "伍佰 作曲 · 制作（词 那英）", "mode": "decouple", "aud": "au_p5", "fseek": 41.0,
     "ch_off": 181.28, "show": 29.0,
     "tag": "天后少见的脆弱", "note": "大嗓的那英，被写出了不逞强的一面"},
    {"key": "p4", "no": "04", "singer": "王菲", "song": "单行道",
     "meta": "伍佰 作曲 · China Blue 编曲演奏", "mode": "decouple", "aud": "au_p4", "fseek": 183.3,
     "ch_off": 272.32, "show": 27.3,
     "tag": "冷知识：王菲也唱过伍佰", "note": "慵懒又疏离，意外地合"},
    {"key": "p3", "no": "03", "singer": "莫文蔚", "song": "坚强的理由",
     "meta": "伍佰 词曲 · 合唱", "mode": "sync",
     "ch_off": 192.3, "show": 40.0,
     "tag": "把坚强，写成快要塌掉", "note": "伍佰 × 莫文蔚 对唱，都市废墟感"},
    {"key": "p2", "no": "02", "singer": "苏慧伦", "song": "被动",
     "meta": "1996 · 专辑《Lemon Tree》 · 伍佰 作曲", "mode": "sync",
     "ch_off": 151.05, "show": 25.0,
     "tag": "听起来温柔，骨子里很倔", "note": "女声唱伍佰，最成功的一次"},
    {"key": "p1", "no": "01", "singer": "王心凌", "song": "我会好好的",
     "meta": "2005 · 专辑《Cyndi With U》 · 伍佰 词曲", "mode": "sync",
     "ch_off": 171.34, "show": 32.7,
     "tag": "甜心体系里，最反甜的一首", "note": "我快不行了，但我会好好的"},
]

MGAIN = {}  # 响度补偿（QA 后微调）

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")
for it in items:
    it["voice_dur"] = dur(A / f"{it['key']}.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for it in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + it["voice_dur"])
    full_start = q(narr_end + POST + DIG)
    end = q(full_start + it["show"])
    seg_dur = q(end - t)
    full_start_local = q(full_start - t)
    narr_end_local = q(LEAD + it["voice_dur"])
    onset_local = q(narr_end_local - ONSET_LEAD)
    aud_start = q(max(0, it["ch_off"] - onset_local))
    fseek = aud_start if it["mode"] == "sync" else q(it.get("fseek", 0.0))
    blocks.append({**it, "start": q(t), "end": end, "narr_start": narr_start,
                   "narr_end": narr_end, "full_start": full_start,
                   "full_start_local": full_start_local, "narr_end_local": narr_end_local,
                   "aud_start": aud_start, "fseek": fseek, "seg_dur": seg_dur})
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)

# 展示段对齐闸门（机械化强制；synced 慢歌可靠，响摇滚降级 WARN）
if not os.environ.get("SKIP_GATE"):
    try:
        sys.path.insert(0, str(ROOT.parents[1]))
        from tools.video import showcase_align
        gate_blocks = [{"clip": (b["aud"] if b["mode"] == "decouple" else f"vert_{b['key']}"),
                        "start": b["start"], "narr_end": b["narr_end"],
                        "full_start": b["full_start"], "end": b["end"], "mseek": b["aud_start"]}
                       for b in blocks]
        showcase_align.gate(gate_blocks, ROOT / "probe" / "vocal_analysis.json",
                            consts=dict(POST=POST, DIG=DIG),
                            plan_path=ROOT / "probe" / "showcase_plan.json")
    except FileNotFoundError:
        print("[gate] vocal_analysis.json 未就绪，跳过（download/probe 后再跑）")


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


def make_footage(out_path, vert, fseek, length):
    """从已竖屏化的 clips/vert_*.mp4 输出端 seek 切 [fseek, fseek+length] 段（不再裁切）。"""
    if HTML_ONLY or AUDIO_ONLY:
        return
    run([
        "ffmpeg", "-v", "error", "-i", str(vert), "-ss", str(fseek), "-t", str(length),
        "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", str(out_path), "-y",
    ])


segments = []

# ---- INTRO ----  低音量床 = #1《我会好好的》副歌（情绪收束），需在下方 BED_SONG 指定可用源
BED_SONG = "p1"  # 用于 intro/outro 床的歌曲 key（其 vert clip 必须存在）
BED_CH = next(b for b in blocks if b["key"] == BED_SONG)
make_footage(CS / "intro.mp4", CLIPS / f"{INTRO_CLIP}.mp4", INTRO_FSEEK, intro_end)
arun([
    "ffmpeg", "-v", "error",
    "-ss", str(BED_CH["ch_off"]), "-i", str(CLIPS / f"vert_{BED_SONG}.mp4"),
    "-i", str(A / "intro.wav"),
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={q(intro_end-0.9)}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

# ---- SONG SEGMENTS ----
for b in blocks:
    make_footage(CS / f"{b['key']}.mp4", CLIPS / f"vert_{b['key']}.mp4", b["fseek"], b["seg_dur"])
    env = envelope(b["narr_end_local"], b["full_start_local"])
    mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    if b["mode"] == "sync":
        music_in = str(CLIPS / f"vert_{b['key']}.mp4")
    else:
        music_in = str(RAW / f"{b['aud']}.mp3")
    arun([
        "ffmpeg", "-v", "error",
        "-ss", str(b["aud_start"]), "-i", music_in,
        "-i", str(A / f"{b['key']}.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{b['seg_dur']},volume='{env}':eval=frame,volume={mg}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['seg_dur']},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

# ---- OUTRO ----
outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
make_footage(CS / "outro.mp4", CLIPS / f"{OUTRO_CLIP}.mp4", OUTRO_FSEEK, outro_dur)
arun([
    "ffmpeg", "-v", "error",
    "-ss", str(BED_CH["ch_off"]), "-i", str(CLIPS / f"vert_{BED_SONG}.mp4"),
    "-i", str(A / "outro.wav"),
    "-i", str(A / "outro_cta.wav"),
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.17,afade=t=in:st=0:d=0.9,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{n}'\n" for n in segments), encoding="utf-8")
arun([
    "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
    "-af", f"volume={MASTER_GAIN},alimiter=limit=0.97",
    "-ac", "2", "-ar", "48000", "master.wav", "-y",
])
if not HTML_ONLY:
    print("master dur:", dur(ROOT / "master.wav"), "planned:", total)

# 渲染占位静音轨（真音频后期 mux）
if not (ROOT / "silent.m4a").exists() or not HTML_ONLY:
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", str(total), "-c:a", "aac", "-b:a", "16k", str(ROOT / "silent.m4a"), "-y",
    ], cwd=ROOT, check=True)

# 单一 footage 轨：把 12 段按时间线拼成一条连续视频，HTML 只挂 1 个 <video>
foot_order = ["intro"] + [b["key"] for b in blocks] + ["outro"]
if not (CS / "footage_track.mp4").exists() or not HTML_ONLY:
    (ROOT / "foottrack.txt").write_text(
        "".join(f"file 'clips_seg/{k}.mp4'\n" for k in foot_order), encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "foottrack.txt",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", "-an",
        str(CS / "footage_track.mp4"), "-y",
    ], cwd=ROOT, check=True)

# ============================ HTML ============================
ACC = "#ff6585"      # 玫瑰红主强调
ACC2 = "#7c9fce"     # 冷蓝副
GOLD = "#ffce5a"     # 第一名金
BASE = "#08060d"

videos = [
    f'<video id="footage" class="clip fv" data-start="0" data-duration="{total}" '
    f'data-track-index="0" src="clips_seg/footage_track.mp4" muted playsinline></video>'
]

labels, tweens = [], []
for idx, b in enumerate(blocks):
    fid, mid = f"full{idx}", f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    top = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip card{top}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">NO.<b>{b["no"]}</b></div>'
        f'<div class="singer">{b["singer"]}</div>'
        f'<h2 class="song">《{b["song"]}》</h2>'
        f'<div class="meta">{b["meta"]}</div>'
        f'<p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip mini{top}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["singer"]}《{b["song"]}》</strong></section>'
    )
    s, fs, e = b["start"], b["full_start"], b["end"]
    tweens.append(f'tl.fromTo("#{fid} .rank",{{x:-30,opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power3.out"}},{q(s+.18)});')
    tweens.append(f'tl.fromTo("#{fid} .singer",{{x:-20,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"sine.out"}},{q(s+.4)});')
    tweens.append(f'tl.fromTo("#{fid} .song",{{y:42,opacity:0}},{{y:0,opacity:1,duration:.62,ease:"power3.out"}},{q(s+.54)});')
    tweens.append(f'tl.fromTo("#{fid} .meta",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power1.out"}},{q(s+.8)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power1.out"}},{q(s+1.0)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:16,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+1.24)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{q(fs-.45)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(fs)});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-26,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(fs+.12)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(e-.4)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{q(e)});')

transition_divs, transition_tweens = [], []
for i, b in enumerate(blocks):
    tid = f"tr{i}"
    ts = q(max(0, b["start"] - 0.15))
    transition_divs.append(f'<div id="{tid}" class="clip trans" data-start="{ts}" data-duration="0.9" data-track-index="8"></div>')
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.6,scaleY:.05}},{{opacity:0,scaleY:1,duration:.8,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li{" class=top" if b["no"]=="01" else ""}><span>{b["no"]}</span><strong>{b["singer"]}《{b["song"]}》</strong></li>'
    for b in blocks
)

css = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
@font-face{{font-family:"PingFang SC";src:local("PingFang SC");font-weight:100 900}}
@font-face{{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:{BASE};
  font-family:"PingFang SC",system-ui,sans-serif;color:#f4f0ea;-webkit-font-smoothing:antialiased}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{BASE}}}
.fv{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}}
#scrim{{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,6,13,.86),rgba(8,6,13,.10) 30%,rgba(8,6,13,.28) 60%,rgba(5,3,9,.95))}}
#vig{{position:absolute;inset:0;z-index:1;box-shadow:inset 0 0 360px rgba(0,0,0,.80)}}
#glow{{position:absolute;inset:-260px;z-index:1;opacity:.5;background:radial-gradient(40% 24% at 18% 16%,rgba(255,101,133,.40),rgba(255,101,133,0) 66%),radial-gradient(46% 30% at 82% 82%,rgba(124,159,206,.26),rgba(124,159,206,0) 70%)}}
#grain{{position:absolute;inset:-20px;z-index:9;opacity:.06;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(244,240,234,.13) 0 1px,rgba(244,240,234,0) 1px 4px)}}
.trans{{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(255,101,133,0),rgba(255,101,133,.6),rgba(124,159,206,0));transform-origin:center}}

#cover{{position:absolute;inset:0;z-index:5;padding:150px 76px 140px;display:flex;flex-direction:column;justify-content:space-between;
  background:linear-gradient(180deg,rgba(8,6,13,.74),rgba(8,6,13,.18) 32%,rgba(8,6,13,.24) 58%,rgba(5,3,9,.92))}}
.brandline{{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:{ACC};letter-spacing:.32em}}
.brandline:before{{content:"";width:64px;height:4px;background:{ACC};border-radius:99px;box-shadow:0 0 20px rgba(255,101,133,.7)}}
#cover h1{{margin-top:28px;font-family:"Songti SC",serif;font-size:118px;line-height:1.1;font-weight:900;text-shadow:0 6px 44px rgba(0,0,0,.66)}}
#cover h1 b{{color:{ACC}}}
#cover .toptag{{display:inline-block;margin-top:26px;font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#f4f0ea;
  letter-spacing:.14em;border:2px solid rgba(255,101,133,.6);border-radius:10px;padding:10px 26px;background:rgba(8,6,13,.5)}}
#cover .sub{{margin-top:30px;font-size:35px;line-height:1.5;color:#e6dde6;font-weight:600;max-width:930px}}
.chips{{display:flex;flex-wrap:wrap;gap:14px;max-width:940px}}
.chips span{{border:1.5px solid rgba(124,159,206,.5);color:#eee7f1;background:rgba(8,6,13,.55);font-size:27px;font-weight:800;padding:11px 18px;border-radius:8px}}

.card{{position:absolute;z-index:5;left:60px;right:60px;bottom:172px;padding:34px 38px 40px;
  background:linear-gradient(135deg,rgba(10,7,16,.92),rgba(24,16,30,.62));border-left:9px solid {ACC};border-radius:8px;
  backdrop-filter:blur(3px);box-shadow:0 24px 74px rgba(0,0,0,.44)}}
.card .rank{{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:800;color:{ACC};letter-spacing:.16em}}
.card .rank b{{font-size:60px;font-weight:900;vertical-align:-6px;margin-left:4px}}
.card .singer{{margin-top:14px;font-size:46px;font-weight:900;color:#f7f1ec;letter-spacing:.04em}}
.card .song{{font-family:"Songti SC",serif;margin-top:6px;font-size:70px;line-height:1.12;font-weight:900;color:#f7f1ec}}
.card .meta{{margin-top:12px;font-size:28px;font-weight:700;color:#b6a6bf;letter-spacing:.02em}}
.card .tag{{margin-top:20px;font-size:39px;line-height:1.3;font-weight:900;color:{ACC}}}
.card .note{{margin-top:11px;font-size:29px;line-height:1.44;font-weight:600;color:#e6dde6}}
.card.topRank{{border-left-color:{GOLD};background:linear-gradient(135deg,rgba(16,12,6,.94),rgba(10,7,16,.66))}}
.card.topRank .rank,.card.topRank .tag{{color:{GOLD}}}

.mini{{position:absolute;z-index:5;top:92px;left:56px;display:flex;align-items:center;gap:16px;padding:13px 22px;
  background:rgba(8,6,13,.72);border:1.5px solid rgba(255,101,133,.6);border-radius:9px}}
.mini span{{font-family:"JetBrains Mono",monospace;font-size:42px;font-weight:900;color:#f4f0ea;background:{BASE};border:1px solid rgba(255,101,133,.55);border-radius:6px;padding:2px 10px;line-height:1.1}}
.mini strong{{font-family:"Songti SC",serif;font-size:33px;font-weight:900;max-width:820px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.mini.topRank{{border-color:rgba(255,206,90,.78)}}
.mini.topRank span{{border-color:rgba(255,206,90,.72);color:{GOLD}}}

#outro{{position:absolute;z-index:5;inset:0;padding:104px 64px 150px;display:flex;flex-direction:column;justify-content:center;
  background:linear-gradient(180deg,rgba(8,6,13,.42),rgba(5,3,9,.9))}}
#outro .small{{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:{ACC};letter-spacing:.2em}}
#outro h2{{font-family:"Songti SC",serif;margin-top:20px;font-size:56px;line-height:1.26;font-weight:900;max-width:940px}}
#outro ol{{margin-top:26px;list-style:none;display:grid;gap:9px;width:100%}}
#outro li{{display:flex;align-items:center;gap:18px;padding:12px 18px;background:rgba(10,7,16,.66);border:1px solid rgba(244,240,234,.12);border-radius:8px}}
#outro li span{{font-family:"JetBrains Mono",monospace;font-size:29px;font-weight:900;color:#f4f0ea;background:{BASE};border:1px solid rgba(255,101,133,.45);border-radius:6px;padding:3px 9px;min-width:54px;text-align:center}}
#outro li strong{{font-family:"Songti SC",serif;font-size:30px;font-weight:900;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
#outro li.top{{background:rgba(255,206,90,.14);border-color:rgba(255,206,90,.5)}}
#outro li.top span{{border-color:rgba(255,206,90,.65);color:{GOLD}}}
#outro .close{{margin-top:24px;font-size:30px;line-height:1.5;color:#e6dde6;font-weight:600}}

#cta{{position:absolute;z-index:6;left:72px;right:72px;bottom:96px;text-align:center;padding:22px;background:rgba(8,6,13,.74);border:1.5px solid rgba(255,206,90,.42);border-radius:10px}}
#cta .v{{font-size:44px;font-weight:900;color:{GOLD};line-height:1.22}}
#cta .f{{margin-top:14px;font-size:33px;font-weight:900;color:{ACC};letter-spacing:.16em}}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="11"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    f'<div><div class="brandline">伍佰 · 幕后创作盘点</div>'
    '<h1>伍佰写给<br>女歌手的<b>10</b>首歌</h1>'
    '<div class="toptag">10 → 1 倒数揭晓</div></div>'
    '<div><p class="sub">写浪人情歌的摇滚浪子，把最细腻的一面，悄悄写进了别人的歌里。</p>'
    '<div class="chips"><span>王菲</span><span>那英</span><span>苏慧伦</span><span>王心凌</span><span>莫文蔚</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">FINAL RANKING</div>'
    '<h2>十个女声，<br>背后是同一个伍佰。</h2>'
    f'<ol>{ranking_rows}</ol>'
    '<p class="close">他从来不只是那个嘶吼的伍佰。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="silent.m4a" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .brandline, #cover h1, #cover .toptag, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.02,duration:3.4,ease:"sine.inOut",yoyo:true,repeat:1}},0.2);
tl.fromTo("#glow",{{x:-18,y:0}},{{x:22,y:-14,duration:{total},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.45,ease:"power1.in"}},{q(intro_end-.55)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(transition_tweens)}
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.66,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-30,opacity:0}},{{x:0,opacity:1,duration:.4,ease:"power2.out",stagger:.08}},{q(outro_start+1.15)});
tl.fromTo("#outro .close",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(outro_start+2.4)});
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
    "id": "main", "name": SLUG, "total": total,
    "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [{"no": b["no"], "singer": b["singer"], "song": b["song"], "mode": b["mode"],
                "start": b["start"], "full_start": b["full_start"], "end": b["end"],
                "fseek": b["fseek"], "aud_start": b["aud_start"], "ch_off": b["ch_off"],
                "seg_dur": b["seg_dur"]} for b in blocks],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
for b in blocks:
    print(b["no"], b["singer"], b["song"], "start", b["start"], "full", b["full_start"], "end", b["end"], "fseek", b["fseek"])
