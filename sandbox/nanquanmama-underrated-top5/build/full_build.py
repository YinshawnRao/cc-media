#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 南拳妈妈最被低估的5首歌.

Countdown 5 -> 1 (#1 = 消失 climax). 选源现实（见 SOURCES.md）：
- 消失 / 破晓 / 离家不远 = 真官方 MV（阿爾發音樂）→ COUPLED：footage 与 audio 同源同窗（fseek=mseek，口型同步）。
  破晓/离家底部卡拉OK烧词裁底；消失 640x356 裁底很窄。
- 人鱼的眼泪 / 最后一枚笑容 = 官方频道上传是静态专辑封面图 + 音频（不是真 MV）
  → DECOUPLED：音频用官方静态版录音室音轨，画面用南拳妈妈本人**其他官方 MV** 救场：
    人鱼←《河流午後我經過》? 不——用《無瑕》(沉郁特写+海边夕照,贴"人鱼/海水/眼泪",冷调微调)；
    最后一枚←《風雪梧桐》(暖棕特写,贴"克制/温柔/散场")。
每段：footage = clips_seg/<key>.mp4（从 fseek 切 seg_dur、内联 letterbox+crop+grade，从 0 播）；
      music = raw/<aud>_aud.wav 从 mseek 切，使副歌(ch_off)恰好落在 full-volume 展示段起点。

Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> render only intro + #5 + outro pilot. HTML_ONLY=1 -> skip media rebuild.
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

# intro/outro 音乐床 = 消失（#1，弦乐+教堂钟声叙事）
INTRO_BED_AUD = "p1"
INTRO_BED_SEEK = 2.0
OUTRO_BED_AUD = "p1"
OUTRO_BED_SEEK = 160.0

# intro/outro 画面底 = 河流午後（南拳妈妈本人乐团镜头，与 cover 呼应；intro 大部分被 cover 遮住）
COVER_FSRC = "fr_hlwh.mp4"
COVER_FSEEK = 60.0
INTRO_FSRC = "fr_hlwh.mp4"
INTRO_FSEEK = 44.0
OUTRO_FSRC = "fr_hlwh.mp4"
OUTRO_FSEEK = 70.0
SIDE_CROP = "640:404:0:0"   # 河流午後 裁底烧词

ACC = "#86b7cf"    # 海蓝强调色
ACC_SOFT = "#bfe0ef"


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def footage_filter(crop, grade=None, bg_blur=30, br=-0.30, sat=1.04):
    g = (grade + ",") if grade else ""
    return (
        f"[0:v]crop={crop},split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma={bg_blur},eq=brightness={br}:saturation={sat}[bgb];"
        f"[fg]{g}scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )


def cut_footage(fsrc, fseek, seg_dur, crop, grade, out):
    """output-precise seek（input-seek 对 HLS/webm 不准）：先 input-seek 到 fseek 前 12s 关键帧，再精确 output-seek。"""
    pre = max(0.0, fseek - 12.0)
    fine = fseek - pre
    run([
        "ffmpeg", "-v", "error", "-ss", str(pre), "-i", str(RAW / fsrc),
        "-ss", str(fine), "-t", str(seg_dur),
        "-filter_complex", footage_filter(crop, grade),
        "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-an", str(out), "-y",
    ])


ITEMS = [
    {
        "key": "p5_lijia", "no": "05", "aud": "p5",
        "name": "《离家不远》", "plain": "离家不远", "meta": "调色盘 · 2006",
        "show": 29.35, "ch_off": 156.22, "mgain": 1.0,
        "fsrc": "p5_lijia.webm", "fseek": None, "crop": "640:396:0:0", "grade": None,
        "tag": "离家不远，家却被留在了身后",
        "note": "弹头写给家人的情歌，唱尽游子的想家",
    },
    {
        "key": "p4_xiaorong", "no": "04", "aud": "p4",
        "name": "《最后一枚笑容》", "plain": "最后一枚笑容", "meta": "2号餐 · 2005",
        "show": 26.45, "ch_off": 186.22, "mgain": 1.0,
        "fsrc": "fr_fxwt.mp4", "fseek": 30.0, "crop": "640:396:0:0", "grade": None,
        "tag": "散场之前，最后一点温柔",
        "note": "弹头一手包办词曲，与 Lara 同唱的克制告别",
    },
    {
        "key": "p3_renyu", "no": "03", "aud": "p3",
        "name": "《人鱼的眼泪》", "plain": "人鱼的眼泪", "meta": "调色盘 · 2006",
        "show": 24.45, "ch_off": 206.50, "mgain": 1.0,
        "fsrc": "fr_wuxia.mp4", "fseek": 168.0, "crop": "640:396:0:0",
        "grade": "colorbalance=rs=-0.05:bs=0.12:bm=0.06,eq=saturation=0.85",
        "tag": "童话、海水，说不出口的遗憾",
        "note": "黄俊郎填词，藏在专辑里的一条蓝色暗线",
    },
    {
        "key": "p2_poxiao", "no": "02", "aud": "p2",
        "name": "《破晓》", "plain": "破晓", "meta": "2号餐 · 2005",
        "show": 31.05, "ch_off": 178.86, "mgain": 1.0,
        "fsrc": "p2_poxiao.mp4", "fseek": None, "crop": "640:396:0:0", "grade": None,
        "tag": "天亮之前的那一点光",
        "note": "电子摇滚揉进古典弦乐，弹头写的励志词",
    },
    {
        "key": "p1_xiaoshi", "no": "01", "aud": "p1",
        "name": "《消失》", "plain": "消失", "meta": "2号餐 · 2005",
        "show": 24.85, "ch_off": 198.97, "mgain": 1.0,
        "fsrc": "p1_xiaoshi.mp4", "fseek": None, "crop": "640:320:0:0", "grade": None,
        "tag": "像地平线一样，辽阔却孤独",
        "note": "周杰伦力挺的主打，最被低估的南拳妈妈",
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
    mseek = q(max(0, item["ch_off"] - full_start_local))   # music slice start (studio audio)
    fseek = mseek if item["fseek"] is None else q(item["fseek"])  # coupled: fseek=mseek (口型同步)
    block = {
        **item,
        "clip": f"vert_{item['key']}",
        "start": q(t), "end": end,
        "narr_start": narr_start, "narr_end": narr_end,
        "full_start": full_start, "full_start_local": full_start_local,
        "mseek": mseek, "fseek": fseek, "seg_dur": q(end - t),
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
sys.path.insert(0, str(ROOT.parents[1]))  # 让 tools 可 import（ROOT.parents[1]=repo root）
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
    # cover_hero.png（河流午後 乐团镜头 letterbox，真人封面底）
    run([
        "ffmpeg", "-v", "error", "-ss", str(COVER_FSEEK), "-i", str(RAW / COVER_FSRC), "-frames:v", "1",
        "-filter_complex", footage_filter(SIDE_CROP, None, bg_blur=22, br=-0.18, sat=1.02),
        "-map", "[v]", str(ROOT / "cover_hero.png"), "-y",
    ])
    # intro footage（大部分被 cover 遮住）
    cut_footage(INTRO_FSRC, INTRO_FSEEK, intro_end, SIDE_CROP, None, CS / "intro.mp4")
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
        cut_footage(block["fsrc"], block["fseek"], block["seg_dur"],
                    block["crop"], block["grade"], seg)
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
    cut_footage(OUTRO_FSRC, OUTRO_FSEEK, outro_dur, SIDE_CROP, None, CS / "outro.mp4")
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
        ("05", "离家不远"),
        ("04", "最后一枚笑容"),
        ("03", "人鱼的眼泪"),
        ("02", "破晓"),
        ("01", "消失"),
    ]
)

css = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
@font-face{{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}}
@font-face{{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#070a10;
  font-family:"PingFang SC",system-ui,sans-serif;color:#eef3f7;-webkit-font-smoothing:antialiased}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#070a10}}
.fv{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}}
#scrim{{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(7,10,16,.90),rgba(7,10,16,.05) 30%,rgba(7,10,16,.18) 55%,rgba(4,6,11,.95))}}
#glow{{position:absolute;inset:-260px;z-index:1;opacity:.40;background:radial-gradient(42% 26% at 18% 16%,rgba(110,170,200,.40),rgba(110,170,200,0) 65%),radial-gradient(48% 30% at 82% 82%,rgba(90,140,180,.26),rgba(90,140,180,0) 68%)}}
#grain{{position:absolute;inset:-20px;z-index:9;opacity:.05;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(238,243,247,.13) 0 1px,rgba(238,243,247,0) 1px 4px)}}
.trans{{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(134,183,207,0),rgba(134,183,207,.50),rgba(90,140,180,0));transform-origin:center}}
#cover{{position:absolute;inset:0;z-index:5;padding:118px 76px 110px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(7,10,16,.80),rgba(7,10,16,.10) 30%,rgba(7,10,16,.24) 60%,rgba(4,6,11,.93))}}
.eyebrow{{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:{ACC};letter-spacing:.10em}}
.eyebrow:before{{content:"";width:58px;height:4px;background:{ACC};border-radius:99px;box-shadow:0 0 18px rgba(134,183,207,.60)}}
#cover h1{{margin-top:28px;font-family:"Songti SC",serif;font-size:106px;line-height:1.1;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.72)}}
#cover h1 b{{color:{ACC_SOFT};font-weight:900}}
#cover .sub{{margin-top:548px;font-size:35px;line-height:1.5;color:#d9e2ea;font-weight:600;max-width:924px;text-shadow:0 3px 20px rgba(0,0,0,.82)}}
.chips{{display:flex;flex-wrap:wrap;gap:14px;max-width:940px}}
.chips span{{border:1.5px solid rgba(134,183,207,.50);color:#e2eef6;background:rgba(7,10,16,.56);font-size:27px;font-weight:800;padding:12px 18px;border-radius:8px}}
.fullLabel{{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(7,10,16,.91),rgba(20,30,42,.56));border-left:8px solid {ACC};border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.38)}}
.fullLabel .rank{{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:{ACC};letter-spacing:.14em}}
.fullLabel .meta{{margin-top:14px;font-size:28px;font-weight:700;color:#9fb4c2;letter-spacing:.06em}}
.fullLabel h2{{font-family:"Songti SC",serif;margin-top:12px;font-size:82px;line-height:1.12;font-weight:900;color:#eef3f7}}
.fullLabel .tag{{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:{ACC_SOFT}}}
.fullLabel .note{{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#d9e2ea}}
.fullLabel.topRank{{border-left-color:#e8c977;background:linear-gradient(135deg,rgba(18,14,8,.93),rgba(7,10,16,.60))}}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{{color:#f0d488}}
.miniLabel{{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(7,10,16,.70);border:1.5px solid rgba(134,183,207,.52);border-radius:8px}}
.miniLabel span{{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#eef3f7;background:#070a10;border:1px solid rgba(134,183,207,.50);border-radius:6px;padding:2px 8px;line-height:1.1}}
.miniLabel strong{{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.miniLabel.topRank{{border-color:rgba(232,201,119,.76)}}
.miniLabel.topRank span{{border-color:rgba(232,201,119,.70)}}
#outro{{position:absolute;z-index:5;inset:0;padding:104px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(7,10,16,.42),rgba(7,10,16,.90))}}
#outro .small{{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:{ACC};letter-spacing:.14em}}
#outro h2{{font-family:"Songti SC",serif;margin-top:20px;font-size:52px;line-height:1.32;font-weight:900;max-width:936px}}
#outro ol{{margin-top:32px;list-style:none;display:grid;gap:13px;width:100%}}
#outro li{{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(7,10,16,.64);border:1px solid rgba(238,243,247,.14);border-radius:8px}}
#outro li span{{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#eef3f7;background:#070a10;border:1px solid rgba(134,183,207,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}}
#outro li:last-child{{background:rgba(232,201,119,.14);border-color:rgba(232,201,119,.45)}}
#outro li:last-child span{{border-color:rgba(232,201,119,.65)}}
#outro li strong{{font-family:"Songti SC",serif;font-size:34px;font-weight:900;text-align:right}}
#outro .close{{margin-top:26px;font-size:30px;line-height:1.5;color:#d9e2ea;font-weight:600}}
#cta{{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px;background:rgba(7,10,16,.72);border:1.5px solid rgba(232,201,119,.42);border-radius:9px}}
#cta .v{{font-size:42px;font-weight:900;color:#f0d488;line-height:1.22}}
#cta .f{{margin-top:14px;font-size:33px;font-weight:900;color:{ACC};letter-spacing:.14em}}
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
    '<div><div class="eyebrow">华语遗珠 · 不只是那个夏天</div><h1>南拳妈妈<br><b>最被低估</b>的5首歌</h1></div>'
    '<div><p class="sub">在《牡丹江》《橘子汽水》那些大热歌之外，他们还藏着更安静、更细腻的另一面。这五首，是最被低估的南拳妈妈。</p>'
    '<div class="chips" style="margin-top:26px"><span>安静叙事</span><span>克制留白</span><span>杰威尔遗珠</span><span>青春暗面</span><span>越听越深</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>南拳妈妈从来不只是那个把夏天唱得又甜又燃的组合，他们也很会用最安静的方式，去写离别、写想家、写孤独。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这些被大热歌盖住的遗珠，刚好补全了他们最细腻、也最被低估的另一面。</p></section>'
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
    "id": "main", "name": "nanquanmama-underrated-top5", "sample": SAMPLE,
    "total": total, "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "aud": b["aud"], "start": b["start"], "narr_start": b["narr_start"],
         "narr_end": b["narr_end"], "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "fseek": b["fseek"], "ch_off": b["ch_off"], "show": b["show"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start, "SAMPLE:", SAMPLE)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"], "fseek", b["fseek"]) for b in blocks])
