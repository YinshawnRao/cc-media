#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 李玟（CoCo Lee）最被低估的5首歌.

Countdown 5 -> 1 (#1 = 默默爱你 climax). 选源现实（见 SOURCES.md）：
- 不爱你了 / 过完冬季 / 默默爱你 = 真官方 MV（本人全程在镜，耦合：footage+音频同源同窗，口型同步）。
- 爱你是大麻烦（Promise 冷门曲，无棚版 MV，官方频道上传是 B&W 户外 Live）→ 解耦：
  录音室音轨 + 《So Crazy》官方 MV（同碟、1080p、红裙俏皮，贴合"轻快遗珠"）。
- 答案（官方 MV 是杨凡电影《美少年之恋》画面，本人几乎不出镜）→ 解耦：
  官方录音室音轨 + 《想你的365天》官方 MV（同碟 1998、紫调本人特写全程在场）。
封面=第一首出场歌（#5）动态画面：intro footage 与 #5 footage 取 So Crazy 连续窗（T0=53），
封面切第一首画面不剪、丝滑（无静态 cover_hero）。

每首 footage = clips/vert_<key>.mp4（已 letterbox，从 0 播）；audio = raw/<aud>_aud.wav。
耦合：footage 与音频都从源 mseek 切（口型同步）；解耦：footage 用各自 fseek 独立切窗。

Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> intro + #5 + outro 样片。HTML_ONLY=1 -> 跳过音频+footage 重建。
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
C.mkdir(exist_ok=True)
CS.mkdir(exist_ok=True)

SAMPLE = os.environ.get("SAMPLE") == "1"
HTML_ONLY = os.environ.get("HTML_ONLY") == "1"
AUDIO_ONLY = os.environ.get("AUDIO_ONLY") == "1"  # 只重建音频+master（复用已切 footage），用于响度微调后 re-mux

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
COVER_T0 = 90.0          # So Crazy 源时间：封面第 0 帧 = 强正脸特写；intro→#5 连续窗起点

# intro 床 = #5 爱你是大麻烦（轻快，引入第一首）；outro 床 = #1 默默爱你 副歌（情感收束）
INTRO_BED_AUD = "p5"
INTRO_BED_SEEK = 96.0
OUTRO_BED_AUD = "p1"
OUTRO_BED_SEEK = 134.0
OUTRO_FOOTAGE = "xiang365"     # 片尾画面：想你的365天 紫调本人特写（反思收束）
OUTRO_FSEEK = 150.0
INTRO_FOOTAGE = "socrazy_h264"


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def vfill_cut(src, off, length, crop, out, bright=-0.32, sat=1.06, fgbr=0.0):
    """从 src 的 off 秒起切 length 秒，crop 后 letterbox 成 1080x1920（模糊背景填充）。
    output-side seek（-i 后 -ss）对 AV1 精确，保证耦合口型同步。fgbr>0 给暗源前景提亮。"""
    fg = "[fg]"
    fgchain = "[fg]scale=1080:-2[fgs]"
    if fgbr:
        fgchain = f"[fg]eq=brightness={fgbr}:saturation=1.08,scale=1080:-2[fgs]"
    filt = (
        f"[0:v]crop={crop},split=2[bg]{fg};"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=30,eq=brightness={bright}:saturation={sat}[bgb];"
        f"{fgchain};"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run([
        "ffmpeg", "-v", "error", "-i", str(src), "-ss", str(q(off)), "-t", str(q(length)),
        "-filter_complex", filt, "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(out), "-y",
    ])


ITEMS = [
    {
        "key": "p5_dmf", "no": "05", "aud": "p5",
        "name": "《爱你是大麻烦》", "plain": "爱你是大麻烦", "meta": "Promise 承诺 · 2001",
        "show": 32.4, "ch_off": 150.4, "mgain": 1.15,
        "footage": "socrazy_h264", "crop": "1920:1080:0:0", "fseek": "intro_cont", "fgbr": 0.0,
        "tag": "爱起来，是甜蜜的麻烦",
        "note": "被主打盖住的轻快遗珠，俏皮又灵动",
    },
    {
        "key": "p4_buai", "no": "04", "aud": "p4",
        "name": "《不爱你了》", "plain": "不爱你了", "meta": "Sunny Day 好心情 · 1998",
        "show": 33.88, "ch_off": 194.24, "mgain": 1.0,
        "footage": "p4_buai", "crop": "640:480:0:0", "fseek": None, "fgbr": 0.0,
        "tag": "不爱了，不是洒脱的口号",
        "note": "关系尽头的清醒与疲惫，越冷越有味",
    },
    {
        "key": "p3_daan", "no": "03", "aud": "p3",
        "name": "《答案》", "plain": "答案", "meta": "Sunny Day 好心情 · 1998",
        "show": 41.61, "ch_off": 159.81, "mgain": 1.0,
        "footage": "xiang365", "crop": "640:480:0:0", "fseek": 45.0, "fgbr": 0.0,
        "tag": "答案，藏在等待里",
        "note": "杨凡电影《美少年之恋》主题曲 · 姚谦词 鲍比达曲",
    },
    {
        "key": "p2_guodong", "no": "02", "aud": "p2",
        "name": "《过完冬季》", "plain": "过完冬季", "meta": "Di Da Di 暗示 · 1998",
        "show": 31.33, "ch_off": 203.67, "mgain": 1.15,
        "footage": "p2_guodong", "crop": "1440:1080:0:0", "fseek": None, "fgbr": 0.0,
        "tag": "冬天过完，心未必放晴",
        "note": "旋律很长、情绪很沉的深情慢歌",
    },
    {
        "key": "p1_momo", "no": "01", "aud": "p1",
        "name": "《默默爱你》", "plain": "默默爱你", "meta": "Sunny Day 好心情 · 1998",
        "show": 30.49, "ch_off": 134.15, "mgain": 1.18,
        "footage": "p1_momo", "crop": "640:480:0:0", "fseek": None, "fgbr": 0.08,
        "tag": "把爱意，默默唱给你",
        "note": "节奏蓝调情歌里，最迷人的李玟",
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
    mseek = q(max(0, item["ch_off"] - full_start_local))  # audio slice start
    # footage source seek
    if item["fseek"] == "intro_cont":
        fseek = q(COVER_T0 + intro_end)        # 接 intro 之后，连续窗
    elif item["fseek"] is None:
        fseek = mseek                          # 耦合：footage 与音频同源同窗（口型同步）
    else:
        fseek = q(item["fseek"])               # 解耦：独立窗
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
sys.path.insert(0, str(ROOT.parents[1]))  # repo root
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


# ---- 切 footage：vert_intro / vert_<key> / vert_outro（letterbox）----
if not HTML_ONLY and not AUDIO_ONLY:
    vfill_cut(RAW / f"{INTRO_FOOTAGE}.mp4", COVER_T0, intro_end + 0.5,
              "1920:1080:0:0", C / "vert_intro.mp4")
    for block in blocks:
        vfill_cut(RAW / f"{block['footage']}.mp4", block["fseek"], block["seg_dur"] + 0.5,
                  block["crop"], C / f"vert_{block['key']}.mp4", fgbr=block.get("fgbr", 0.0))

segments = []

if not HTML_ONLY:
    # ---- intro: footage video-only slice + bed + voice ----
    if not AUDIO_ONLY:
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
        if not AUDIO_ONLY:
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
    if not AUDIO_ONLY:
        vfill_cut(RAW / f"{OUTRO_FOOTAGE}.mp4", OUTRO_FSEEK, outro_dur + 0.5,
                  "640:480:0:0", C / "vert_outro.mp4")
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

if not HTML_ONLY and not AUDIO_ONLY:
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
        ("05", "爱你是大麻烦"),
        ("04", "不爱你了"),
        ("03", "答案"),
        ("02", "过完冬季"),
        ("01", "默默爱你"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0b0807;
  font-family:"PingFang SC",system-ui,sans-serif;color:#f6f1ea;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0b0807}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(11,8,7,.90),rgba(11,8,7,.05) 30%,rgba(11,8,7,.18) 55%,rgba(8,5,4,.95))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.42;background:radial-gradient(42% 26% at 18% 16%,rgba(232,196,111,.40),rgba(232,196,111,0) 65%),radial-gradient(48% 30% at 82% 82%,rgba(214,120,96,.28),rgba(214,120,96,0) 68%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.055;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(246,241,234,.13) 0 1px,rgba(246,241,234,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(232,196,111,0),rgba(232,196,111,.52),rgba(214,120,96,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:120px 76px 116px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(11,8,7,.82),rgba(11,8,7,.10) 30%,rgba(11,8,7,.22) 60%,rgba(8,5,4,.92))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#e8c46f;letter-spacing:.10em}
.eyebrow:before{content:"";width:58px;height:4px;background:#e8c46f;border-radius:99px;box-shadow:0 0 18px rgba(232,196,111,.60)}
#cover h1{margin-top:28px;font-family:"Songti SC",serif;font-size:104px;line-height:1.1;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.70)}
#cover h1 b{color:#f0cf86;font-weight:900}
#cover .sub{margin-top:556px;font-size:35px;line-height:1.5;color:#ece1d3;font-weight:600;max-width:920px;text-shadow:0 3px 20px rgba(0,0,0,.85)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(232,196,111,.50);color:#f4e8d4;background:rgba(11,8,7,.56);font-size:27px;font-weight:800;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(11,8,7,.91),rgba(40,26,18,.58));border-left:8px solid #c79a52;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.40)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e8c46f;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#c2ad94;letter-spacing:.04em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:80px;line-height:1.12;font-weight:900;color:#f6f1ea}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#f0cf86}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#ece1d3}
.fullLabel.topRank{border-left-color:#f0cf86;background:linear-gradient(135deg,rgba(34,22,10,.93),rgba(11,8,7,.62))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f6d98f}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(11,8,7,.70);border:1.5px solid rgba(232,196,111,.50);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#f6f1ea;background:#0b0807;border:1px solid rgba(232,196,111,.48);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(246,217,143,.78)}
.miniLabel.topRank span{border-color:rgba(246,217,143,.72)}
#outro{position:absolute;z-index:5;inset:0;padding:110px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(11,8,7,.42),rgba(11,8,7,.90))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e8c46f;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:52px;line-height:1.34;font-weight:900;max-width:936px}
#outro ol{margin-top:34px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(11,8,7,.64);border:1px solid rgba(246,241,234,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#f6f1ea;background:#0b0807;border:1px solid rgba(232,196,111,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(246,217,143,.15);border-color:rgba(246,217,143,.46)}
#outro li:last-child span{border-color:rgba(246,217,143,.66)}
#outro li strong{font-family:"Songti SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:28px;font-size:30px;line-height:1.5;color:#ece1d3;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px;background:rgba(11,8,7,.72);border:1.5px solid rgba(246,217,143,.44);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f6d98f;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#e8c46f;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 不只是国际天后</div><h1>李玟<br><b>最被低估</b>的5首歌</h1></div>'
    '<div><p class="sub">在那些热辣、国际化的舞曲之外，她还有一把更温柔、更深情的嗓子。这五首，藏着最被低估的李玟。</p>'
    '<div class="chips" style="margin-top:26px"><span>安静深情</span><span>节奏蓝调</span><span>世纪末遗珠</span><span>温柔一面</span><span>越听越深</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>李玟从来不只是那个站在国际舞台上、热辣又耀眼的流行天后，她也很会用最温柔的方式，把深情慢慢唱给你听。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这些被光芒盖住的遗珠，刚好补全了她最安静、也最被低估的另一面。</p></section>'
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
    "id": "main", "name": "liwen-underrated-top5", "sample": SAMPLE,
    "total": total, "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "aud": b["aud"], "footage": b["footage"],
         "start": b["start"], "narr_start": b["narr_start"], "narr_end": b["narr_end"],
         "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "fseek": b["fseek"], "ch_off": b["ch_off"], "show": b["show"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start, "SAMPLE:", SAMPLE)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"], "fseek", b["fseek"]) for b in blocks])
