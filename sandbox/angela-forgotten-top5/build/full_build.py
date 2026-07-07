#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 杨丞琳最被低估的5首歌.

支持「解耦」歌曲（footage 与 music 不同源）：某首给 `music`（studio wav）+ `music_start`
（副歌在该 wav 的源时间）+ `foot_seek`（footage 在 vert clip 的起点），则该首音乐用 studio
音轨、画面用 Live footage（口型不强求，用于无棚版 MV 的救场）。其余为耦合（footage 自带音轨=音乐）。
"""
import contextlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path


def dur(wav):
    with contextlib.closing(wave.open(str(wav), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
CLIPS = ROOT / "clips"
CLIPS_SEG = ROOT / "clips_seg"
CLIPS_SEG.mkdir(exist_ok=True)
RAW = ROOT / "raw"

TITLE = "张韶涵自己都忘了的5首歌"
SLUG = "angela-forgotten-top5"

LEAD = 0.3
POST = 0.2
DIG = 1.6
BED = 0.14
VOICE_GAIN = 2.0
INTRO_END = 22.0
INTRO_VOICE = 1.2
COVER_END = 6.4
INTRO_CLIP = "vert_p5_shangri"  # 片头底片 = 第一首出场歌《伤日快乐》婚纱MV，连续流入 #5
INTRO_MEDIA_START = 43.56        # = #5 media_seek(65.56) - INTRO_END(22) → 封面→#5 同源连续帧
CTA_GAP = 1.0
OUTRO_TAIL = 2.5
# 片尾：画面复用《伤日快乐》婚纱片（与片头呼应、明亮）；音床用《瞬间移动》录音室音轨（压轴曲、干净，
# 不用 #1 fancam 自带的现场回声音轨）
OUTRO_FOOT_SEEK = 150.0
OUTRO_BED_MUSIC = "shun_audio.wav"
OUTRO_BED_SEEK = 34.91
# 暗调/安静歌补偿（副歌响度对齐 ~-15dB）；loudnorm 后仍偏轻的再抬
MGAIN = {}

SONGS = [
    {
        "key": "p5_shangri",
        "clip": "vert_p5_shangri",
        "no": "05",
        "name": "《伤日快乐》",
        "plain": "伤日快乐",
        "year": "2011 · 幸福最晴天",
        "credit": "偶像剧《幸福最晴天》片尾曲",
        # 耦合：婚纱MV画面 + 自带录音室音轨（前扩到 78.8 副歌入点，收在 129.7 句末）
        "show_start": 82.51,
        "show": 47.2,
        "tag": "默默过生日的那首伤日歌",
        "note": "剧粉还记得，路人却忘了，时间把热度冲淡。",
    },
    {
        "key": "p4_niannian",
        "clip": "vert_p4_niannian",
        "no": "04",
        "name": "《念念》",
        "plain": "念念",
        "year": "近年 · 为歌而赞",
        "credit": "《为歌而赞》舞台上被重新唱起",
        # 耦合：浙江卫视官方 Live（取张韶涵本人演唱段，前扩到 t61，收在 102 句末，避开 t124 男嘉宾返场）
        "show_start": 65.0,
        "show": 37.85,
        "tag": "好听，却没成名场面",
        "note": "她可能没忘，但路人基本没存档。",
    },
    {
        "key": "p3_juebu",
        "clip": "vert_p3_juebu",
        "no": "03",
        "name": "《绝不》",
        "plain": "绝不",
        "year": "2007",
        "credit": "《加油好男儿》主题曲 ·《爱杀17》插曲",
        # 解耦：无棚版 MV → 录音室音轨(歌詞版) + 2007 加油好男儿 Live 画面
        # music_seek 钳到 0 → 展示段=raw[18.28..]，收在 57.1-60.3 器乐 gap(show_end 58.3)；footage 102s 限 foot_seek=40
        "music": "juebu_audio.wav",
        "music_start": 14.38,
        "foot_seek": 40.0,
        "show": 40.0,
        "tag": "用力喊过，却被时代盖过",
        "note": "淹没在她早期那一大批剧歌里。",
    },
    {
        "key": "p2_kongzhi",
        "clip": "vert_p2_kongzhi",
        "no": "02",
        "name": "《控制不了》",
        "plain": "控制不了",
        "year": "2007",
        "credit": "广告单曲 · 有官方MV",
        # 耦合：官方 MV（B站4K修复）画面 + 自带音轨（后扩到 161.7 句末）
        "show_start": 120.33,
        "show": 41.4,
        "tag": "老粉一听前奏就想起来",
        "note": "快歌太多，这一首定位太边缘。",
    },
    {
        "key": "p1_shunjian",
        "clip": "vert_p1_shunjian",
        "no": "01",
        "name": "《瞬间移动》",
        "plain": "瞬间移动",
        "year": "2010",
        "credit": "个人单曲 · 几乎无人记得",
        # 解耦：无 MV → 录音室音轨 + 2026 玩家巡演 Live 画面（后扩到 77.2 句末）
        "music": "shun_audio.wav",
        "music_start": 34.91,
        "foot_seek": 38.0,
        "show": 42.3,
        "tag": "歌名很会跑，热度没跟上",
        "note": "像跑进了另一个平行宇宙，连她都快弄丢。",
    },
]

RANKING_ROWS = [
    ("01", "瞬间移动"),
    ("02", "控制不了"),
    ("03", "绝不"),
    ("04", "念念"),
    ("05", "伤日快乐"),
]

OUTRO_KEY = SONGS[-1]["key"]   # 片尾底片/床 = 压轴《冷战》

meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
d_intro = dur(AUDIO / "intro.wav")
d_outro = dur(AUDIO / "outro.wav")
d_cta = dur(AUDIO / "cta.wav")
for item in SONGS:
    item["voice_dur"] = dur(AUDIO / f"{item['key']}.wav")
    item["narration"] = meta[item["key"]]["text"]

blocks = []
t = INTRO_END
for item in SONGS:
    seg_len = q(LEAD + item["voice_dur"] + POST + DIG + item["show"])
    full_start_local = LEAD + item["voice_dur"] + POST + DIG
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + POST + DIG)
    end = q(t + seg_len)
    decoupled = bool(item.get("music"))
    if decoupled:
        foot_seek = item["foot_seek"]
        music_seek = q(item["music_start"] - full_start_local)
        music_key = Path(item["music"]).stem
    else:
        foot_seek = q(item["show_start"] - full_start_local)
        music_seek = None
        music_key = None
    blocks.append({
        **item, "start": q(t), "end": end, "seg_len": seg_len,
        "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start,
        "mseek": max(0.0, q(foot_seek)),
        "music_seek": None if music_seek is None else max(0.0, music_seek),
        "music_key": music_key, "decoupled": decoupled,
    })
    t = end

outro_start = q(t)
cta_local = q(LEAD + d_outro + CTA_GAP)
outro_len = q(cta_local + d_cta + OUTRO_TAIL)
total = q(outro_start + outro_len)

# ---- 展示段对齐闸门（机械化强制；解耦首用 studio 音轨的人声基准）----
if os.environ.get("ZX_PART", "") == "":
    sys.path.insert(0, str(ROOT.parents[1]))
    from tools.video import showcase_align
    gate_blocks = []
    for b in blocks:
        if b["decoupled"]:
            gate_blocks.append({**b, "clip": b["music_key"], "mseek": b["music_seek"]})
        else:
            gate_blocks.append(b)
    showcase_align.gate(gate_blocks, ROOT / "probe" / "vocal_analysis.json",
                        consts=dict(POST=POST, DIG=DIG),
                        plan_path=ROOT / "probe" / "showcase_plan.json")

PART = os.environ.get("ZX_PART", "")
SPLIT = 2
if PART == "A":
    offset = 0.0
    include_intro = True
    include_outro = False
    selected = blocks[:SPLIT]
    part_duration = blocks[SPLIT - 1]["end"]
    outfile = "segments/partA.html"
    script_src = "../vendor/gsap.min.js"
elif PART == "B":
    offset = blocks[SPLIT]["start"]
    include_intro = False
    include_outro = True
    selected = blocks[SPLIT:]
    part_duration = q(total - offset)
    outfile = "segments/partB.html"
    script_src = "../vendor/gsap.min.js"
else:
    offset = 0.0
    include_intro = True
    include_outro = True
    selected = blocks
    part_duration = total
    outfile = "index.html"
    script_src = "vendor/gsap.min.js"

(ROOT / "segments").mkdir(exist_ok=True)


def E(value):
    return q(value - offset)


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


if PART == "":
    run([
        "ffmpeg", "-v", "error", "-ss", str(INTRO_MEDIA_START), "-i", f"{CLIPS}/{INTRO_CLIP}.mp4",
        "-t", str(INTRO_END), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", "-c:a", "aac", "-b:a", "192k",
        f"{CLIPS_SEG}/intro_clip.mp4", "-y",
    ])

    for b in blocks:
        run([
            "ffmpeg", "-v", "error", "-ss", str(b["mseek"]), "-i", f"{CLIPS}/{b['clip']}.mp4",
            "-t", str(b["seg_len"]), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-g", "30", "-keyint_min", "30", "-c:a", "aac", "-b:a", "192k",
            f"{CLIPS_SEG}/{b['key']}.mp4", "-y",
        ])
        # 解耦首：从 studio 音轨预切 music_seg（与 footage 独立）
        if b["decoupled"]:
            run([
                "ffmpeg", "-v", "error", "-ss", str(b["music_seek"]), "-i", f"{RAW}/{b['music']}",
                "-t", str(b["seg_len"]), "-ac", "2", "-ar", "48000",
                f"music_seg_{b['key']}.wav", "-y",
            ])

    # 片尾 footage（复用婚纱片，时长 = outro_len）
    run([
        "ffmpeg", "-v", "error", "-ss", str(OUTRO_FOOT_SEEK), "-i", f"{CLIPS}/{INTRO_CLIP}.mp4",
        "-t", str(outro_len), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", "-c:a", "aac", "-b:a", "192k",
        f"{CLIPS_SEG}/outro_clip.mp4", "-y",
    ])

    segments = []
    intro_env = (
        f"(lt(t,0.8))*(0.12*t/0.8)"
        f"+(between(t,0.8,{INTRO_VOICE+d_intro+0.8}))*0.12"
        f"+(between(t,{INTRO_VOICE+d_intro+0.8},{INTRO_END}))*(0.12+0.10*(t-{INTRO_VOICE+d_intro+0.8})/{max(0.5, INTRO_END-(INTRO_VOICE+d_intro+0.8))})"
    )
    run([
        "ffmpeg", "-v", "error",
        "-i", f"{CLIPS_SEG}/intro_clip.mp4",
        "-i", f"{AUDIO}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE*1000)}|{int(INTRO_VOICE*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{INTRO_END},volume='{intro_env}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ])
    segments.append("seg_intro.wav")

    for b in blocks:
        narr_end_local = q(LEAD + b["voice_dur"])
        full_start_local = q(b["full_start"] - b["start"])
        env = song_envelope(narr_end_local, full_start_local)
        mgain = MGAIN.get(b["key"], 1.0)
        music_in = f"music_seg_{b['key']}.wav" if b["decoupled"] else f"{CLIPS_SEG}/{b['key']}.mp4"
        out = f"seg_{b['key']}.wav"
        run([
            "ffmpeg", "-v", "error",
            "-i", music_in,
            "-i", f"{AUDIO}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{b['seg_len']},volume='{env}':eval=frame,volume={mgain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['seg_len']},alimiter=level=disabled:limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ])
        segments.append(out)

    run([
        "ffmpeg", "-v", "error",
        "-ss", str(OUTRO_BED_SEEK), "-i", f"{RAW}/{OUTRO_BED_MUSIC}",
        "-i", f"{AUDIO}/outro.wav",
        "-i", f"{AUDIO}/cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)},volume={VOICE_GAIN}[vc];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_len},volume=0.18,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_len-1.6)}:d=1.6[music];"
        f"[vo][vc][music]amix=inputs=3:normalize=0:duration=longest,atrim=0:{outro_len},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ])
    segments.append("seg_outro.wav")

    (ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
    master_dur = dur(ROOT / "master.wav")
    (ROOT / "build" / "timeline.json").write_text(json.dumps({"total": master_dur, "partA": blocks[SPLIT - 1]["end"], "partB": q(master_dur - blocks[SPLIT]["start"]), "split_at": blocks[SPLIT]["start"], "blocks": blocks}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("master dur:", master_dur, "/ planned:", total)

footage = []
if include_intro:
    footage.append(("clips_seg/intro_clip", 0.0, INTRO_END))
for b in selected:
    footage.append((f"clips_seg/{b['key']}", b["start"], b["seg_len"]))
if include_outro:
    footage.append(("clips_seg/outro_clip", outro_start, outro_len))

# 单 footage_track（硬规则）：按时间线顺序 concat 成一条，HTML 只挂 1 个 <video>，避免多 video 帧0挂死
if PART == "":
    (ROOT / "footage_seglist.txt").write_text(
        "".join(f"file '{src}.mp4'\n" for src, _, _ in footage), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "footage_seglist.txt",
         "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
         "-an", f"{CLIPS_SEG}/footage_track.mp4", "-y"])

videos = f'<video id="ftrack" class="fv" data-start="0" data-duration="{part_duration}" data-track-index="0" src="clips_seg/footage_track.mp4" muted playsinline></video>'

labels = []
tweens = []
for b in selected:
    fid = f"lf{b['no']}"
    mid = f"lm{b['no']}"
    label_start = q(b["start"] + 0.25)
    label_dur = q(b["full_start"] - label_start)
    mini_dur = q(b["end"] - b["full_start"])
    top = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip labelFull{top}" data-start="{E(label_start)}" data-duration="{label_dur}" data-track-index="2">'
        f'<div class="rank"><span class="no">{b["no"]}</span><span class="lab">她自己都忘了</span></div>'
        f'<h2>{b["name"]}</h2><p class="yr">{b["year"]}</p><p class="credit">{b["credit"]}</p>'
        f'<p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip labelMini{top}" data-start="{E(b["full_start"])}" data-duration="{mini_dur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.extend([
        f'tl.from("#{fid} .no",{{y:52,opacity:0,duration:.62,ease:"power3.out"}},{E(label_start + 0.06)});',
        f'tl.from("#{fid} .lab",{{x:-20,opacity:0,duration:.45,ease:"power2.out"}},{E(label_start + 0.28)});',
        f'tl.from("#{fid} h2",{{y:42,opacity:0,duration:.62,ease:"power3.out"}},{E(label_start + 0.38)});',
        f'tl.from("#{fid} .yr",{{y:16,opacity:0,duration:.42,ease:"power2.out"}},{E(label_start + 0.62)});',
        f'tl.from("#{fid} .credit",{{y:14,opacity:0,duration:.42,ease:"power2.out"}},{E(label_start + 0.8)});',
        f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{E(label_start + 0.98)});',
        f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{E(label_start + 1.2)});',
        f'tl.to("#{fid}",{{opacity:0,duration:.38,ease:"power1.in"}},{E(b["full_start"] - 0.4)});',
        f'tl.set("#{fid}",{{opacity:0}},{E(b["full_start"])});',
        f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.48,ease:"power2.out"}},{E(b["full_start"] + 0.1)});',
        f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{E(b["end"] - 0.42)});',
        f'tl.set("#{mid}",{{opacity:0}},{E(b["end"])});',
    ])

intro_html = ""
intro_tweens = []
if include_intro:
    intro_html = f"""
<section id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="8">
  <div class="kicker">张韶涵 · 被她照淡的歌</div>
  <h1>张韶涵</h1>
  <div class="h1sub"><em>自己都忘了的</em>5首歌</div>
  <p>强光之下，被她自己照淡的五首歌。</p>
</section>
<section id="hook" class="clip" data-start="7.0" data-duration="6.4" data-track-index="4">
  <div class="hookK">先别急着想她的代表作</div>
  <div class="hookT">真正被遗忘的，<br>是这五首。</div>
</section>
<section id="bridge" class="clip" data-start="15.3" data-duration="5.8" data-track-index="5">
  <small>从第五名到第一名</small>
  <strong>越往后，越遥远</strong>
</section>
"""
    intro_tweens = [
        'tl.set("#cover",{opacity:1},0);',
        'tl.set("#cover .kicker,#cover h1,#cover .h1sub,#cover p",{opacity:1},0);',
        'tl.from("#cover .kicker",{y:-14,duration:.55,ease:"power2.out"},.08);',
        'tl.from("#cover h1",{scale:.985,y:18,duration:.8,ease:"power3.out"},.12);',
        'tl.from("#cover .h1sub",{y:16,duration:.6,ease:"power3.out"},.34);',
        'tl.from("#cover p",{y:18,duration:.58,ease:"power2.out"},.5);',
        f'tl.to("#cover",{{opacity:0,duration:.8,ease:"power1.inOut"}},{COVER_END - .8});',
        f'tl.set("#cover",{{opacity:0}},{COVER_END});',
        'tl.from("#hook .hookK",{x:-24,opacity:0,duration:.48,ease:"power2.out"},7.1);',
        'tl.from("#hook .hookT",{y:26,opacity:0,duration:.62,ease:"power3.out"},7.45);',
        'tl.to("#hook",{opacity:0,duration:.4,ease:"power1.in"},12.9);',
        'tl.set("#hook",{opacity:0},13.3);',
        'tl.from("#bridge small",{y:14,opacity:0,duration:.42,ease:"power2.out"},15.45);',
        'tl.from("#bridge strong",{scale:.86,opacity:0,duration:.62,ease:"back.out(1.5)"},15.72);',
        'tl.to("#bridge",{opacity:0,duration:.45,ease:"power1.in"},20.55);',
        'tl.set("#bridge",{opacity:0},21.0);',
    ]

outro_html = ""
outro_tweens = []
if include_outro:
    rows = "".join(f'<li class="{"gold" if n == "01" else ""}" id="rr{n}"><span>{n}</span><strong>{name}</strong></li>' for n, name in RANKING_ROWS)
    cta_start_abs = q(outro_start + cta_local)
    outro_html = f"""
<section id="outro" class="clip" data-start="{E(outro_start + 0.3)}" data-duration="{q(outro_len - 0.3)}" data-track-index="9">
  <div class="small">完整榜单</div>
  <h2>不是它们不够好，<br>是她的光，太亮了。</h2>
  <ol>{rows}</ol>
</section>
<section id="ctaBar" class="clip" data-start="{E(cta_start_abs - 0.35)}" data-duration="{q(total - cta_start_abs + 0.35)}" data-track-index="10">
  <div>你最想为哪一首投票？</div>
  <p>点赞 · 收藏 · 关注</p>
</section>
"""
    intro_o = E(outro_start + 0.7)
    outro_tweens = [
        f'tl.from("#outro .small",{{x:-22,opacity:0,duration:.45,ease:"power2.out"}},{intro_o});',
        f'tl.from("#outro h2",{{y:30,opacity:0,duration:.65,ease:"power3.out"}},{E(outro_start + 1.1)});',
        *[
            f'tl.from("#rr{n}",{{x:-30,opacity:0,duration:.48,ease:"power3.out"}},{E(outro_start + 5.8 + i * .78)});'
            for i, n in enumerate(["05", "04", "03", "02", "01"])
        ],
        f'tl.from("#ctaBar",{{y:30,opacity:0,duration:.55,ease:"power3.out"}},{E(cta_start_abs - 0.2)});',
    ]

audio_tag = ""
if PART == "":
    audio_tag = f'<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07121a;color:#eaf5f7;font-family:sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07121a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(5,12,18,.82),rgba(5,12,18,.05) 30%,rgba(5,12,18,.16) 56%,rgba(5,12,18,.90))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(122% 78% at 50% 42%,rgba(0,0,0,0) 45%,rgba(0,0,0,.58) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.06;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;z-index:8;inset:0;padding:120px 76px 0;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;text-align:center}
.kicker{font-size:31px;font-weight:800;letter-spacing:.22em;color:#76d3e0;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#cover h1{margin-top:22px;font-family:serif;font-size:150px;line-height:1.0;font-weight:900;letter-spacing:.04em;text-shadow:0 8px 42px rgba(0,0,0,.74)}
.h1sub{margin-top:14px;font-family:serif;font-size:78px;line-height:1.06;font-weight:900;color:#eef7f9;text-shadow:0 8px 36px rgba(0,0,0,.7)}
.h1sub em{font-style:normal;color:#76d3e0}
#cover p{margin-top:30px;max-width:880px;font-size:37px;line-height:1.5;font-weight:550;color:#d9eaee;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#hook{position:absolute;z-index:5;left:76px;right:76px;top:320px}
.hookK{font-size:31px;font-weight:800;letter-spacing:.18em;color:#76d3e0}
.hookK:before{content:"";display:inline-block;width:54px;height:3px;background:#76d3e0;border-radius:3px;margin-right:18px;vertical-align:middle}
.hookT{margin-top:34px;font-family:serif;font-size:80px;line-height:1.28;font-weight:800;color:#eef7f9}
#bridge{position:absolute;z-index:5;left:76px;right:76px;top:50%;transform:translateY(-50%);text-align:center}
#bridge small{display:block;font-size:40px;font-weight:800;letter-spacing:.24em;color:#93b8c0;margin-bottom:24px}
#bridge strong{display:block;font-family:serif;font-size:104px;line-height:1.08;color:#76d3e0;text-shadow:0 8px 44px rgba(0,0,0,.55)}
.labelFull{position:absolute;z-index:5;left:70px;right:70px;bottom:182px;padding:34px 40px 40px;background:linear-gradient(135deg,rgba(9,19,27,.88),rgba(9,19,27,.42));border-left:7px solid #76d3e0;border-radius:8px;backdrop-filter:blur(3px)}
.labelFull .rank{display:flex;align-items:flex-end;gap:20px}
.labelFull .no{font-size:120px;line-height:.82;font-weight:900;color:#a9e7ef;font-family:sans-serif}
.labelFull .lab{font-size:30px;font-weight:800;letter-spacing:.16em;color:#93b8c0;padding-bottom:14px}
.labelFull h2{font-family:serif;margin-top:16px;font-size:82px;line-height:1.05;font-weight:900;color:#fff}
.labelFull .yr{margin-top:12px;font-size:27px;font-weight:600;letter-spacing:.04em;color:#86aeb6}
.labelFull .credit{margin-top:8px;font-size:26px;font-weight:500;letter-spacing:.02em;color:#7896a0}
.labelFull .tag{margin-top:18px;font-size:42px;line-height:1.24;font-weight:850;color:#76d3e0}
.labelFull .note{margin-top:14px;font-size:31px;line-height:1.42;font-weight:520;color:#d4e6ea}
.labelFull.topRank{border-left-color:#ffd27a}
.labelFull.topRank .no,.labelFull.topRank .tag{color:#ffd27a}
.labelMini{position:absolute;z-index:5;top:96px;left:60px;display:flex;align-items:center;gap:16px;padding:12px 22px;background:rgba(9,19,27,.66);border:1px solid rgba(118,211,224,.55);border-radius:999px}
.labelMini span{font-size:42px;font-weight:900;color:#76d3e0}
.labelMini strong{font-family:serif;font-size:38px;font-weight:850;color:#fff}
.labelMini.topRank{border-color:rgba(255,210,122,.72)}
.labelMini.topRank span{color:#ffd27a}
#outro{position:absolute;z-index:9;inset:0;padding:122px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;letter-spacing:.20em;color:#76d3e0}
#outro h2{font-family:serif;margin-top:20px;font-size:66px;line-height:1.2;font-weight:850;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 28px;background:rgba(9,19,27,.64);border:1px solid rgba(255,255,255,.12);border-radius:9px}
#outro li span{font-size:34px;font-weight:900;color:#76d3e0}
#outro li strong{font-family:serif;font-size:40px;font-weight:850;color:#fff}
#outro li.gold{border-color:rgba(255,210,122,.58);background:rgba(46,38,18,.55)}
#outro li.gold span{color:#ffd27a}
#ctaBar{position:absolute;z-index:10;left:60px;right:60px;bottom:118px;padding:34px 40px 38px;text-align:center;background:linear-gradient(135deg,rgba(118,211,224,.20),rgba(9,19,27,.90));border:1px solid rgba(118,211,224,.62);border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar div{font-size:48px;line-height:1.22;font-weight:900;color:#fff}
#ctaBar p{margin-top:20px;font-size:36px;font-weight:850;letter-spacing:.12em;color:#a9e7ef}
"""

body = "\n".join([
    videos,
    f'<div id="scrim" class="clip" data-start="0" data-duration="{part_duration}" data-track-index="1"></div>',
    f'<div id="vig" class="clip" data-start="0" data-duration="{part_duration}" data-track-index="11"></div>',
    f'<div id="grain" class="clip" data-start="0" data-duration="{part_duration}" data-track-index="12"></div>',
    intro_html,
    "\n".join(labels),
    outro_html,
    audio_tag,
])

js = "\n".join([
    "const tl = gsap.timeline({ paused: true });",
    *intro_tweens,
    *tweens,
    *outro_tweens,
    "window.__timelines = window.__timelines || {};",
    'window.__timelines["main"] = tl;',
])

html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{TITLE}</title>
  <script src="{script_src}"></script>
  <style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{part_duration}" data-width="1080" data-height="1920">
    {body}
  </div>
  <script>{js}</script>
</body>
</html>
"""
(ROOT / outfile).write_text(html, encoding="utf-8")
print("wrote", outfile, "duration", part_duration)
