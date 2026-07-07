#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 王力宏最中国风的5首歌.

Countdown 5 -> 1 (#1 = 花田错 climax). 五首全部 COUPLED（footage + 音频同源官方 MV）：
- 画面 = clips/vert_<key>.mp4（已 letterbox，从源 0 起），build 用输出端 seek 切 [mseek..mseek+seg_dur]。
- 音频 = raw/<aud>_aud.wav（从同一官方 MV 抽的整轨），同样 mseek 切 → footage 与音频源时间对齐，口型同步。
封面 = 第一首出场歌《伯牙绝弦》动态画面（INTRO_SEEK 起的 王力宏 侧脸特写），无静态 cover_hero。
选源/crop/展示段窗见 SOURCES.md。

Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> intro + #5 + outro pilot. HTML_ONLY=1 -> skip audio/clip rebuild.
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

# 封面/片头 footage = 伯牙绝弦（#5，第一首出场）王力宏侧脸特写起；片尾 footage = 心中的日月金色采风远景
INTRO_FOOT_CLIP = "vert_p5_boya"
INTRO_SEEK = 62.4
OUTRO_FOOT_CLIP = "vert_p3_riyue"
OUTRO_SEEK = 95.0

# 音乐床：intro 用花田错(#1)钩子做低音量铺垫；outro 用花田错副歌铺到底再 fade
INTRO_BED_AUD = "p1"
INTRO_BED_SEEK = 113.0
OUTRO_BED_AUD = "p1"
OUTRO_BED_SEEK = 131.99


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


ITEMS = [
    {
        "key": "p5_boya", "no": "05", "aud": "p5",
        "name": "《伯牙绝弦》", "plain": "伯牙绝弦", "meta": "十八般武艺 · 2010",
        "show": 22.18, "ch_off": 165.54, "mgain": 0.9,
        "tag": "知音难觅，弦断有谁听",
        "note": "《恋爱通告》概念主题曲，后期中国风里最完整的一首",
    },
    {
        "key": "p4_zhulin", "no": "04", "aud": "p4",
        "name": "《竹林深处》", "plain": "竹林深处", "meta": "心中的日月 · 2007",
        "show": 32.62, "ch_off": 49.77, "mgain": 1.0,
        "tag": "竹林里，凭空开了个录音棚",
        "note": "藏地吟唱、中国鼓、笛声，压进一段很潮的律动",
    },
    {
        "key": "p3_riyue", "no": "03", "aud": "p3",
        "name": "《心中的日月》", "plain": "心中的日月", "meta": "心中的日月 · 2007",
        "show": 27.68, "ch_off": 60.73, "mgain": 1.05,
        "tag": "山川、远方，辽阔的民族色彩",
        "note": "走遍西藏新疆内蒙云南采风，中国风的精神母题",
    },
    {
        "key": "p2_meibian", "no": "02", "aud": "p2",
        "name": "《在梅边》", "plain": "在梅边", "meta": "盖世英雄 · 2005",
        "show": 41.11, "ch_off": 183.93, "mgain": 1.0,
        "tag": "五十秒，二百五十九个字",
        "note": "取材昆曲《牡丹亭》，最有野心的一次实验",
    },
    {
        "key": "p1_huatian", "no": "01", "aud": "p1",
        "name": "《花田错》", "plain": "花田错", "meta": "盖世英雄 · 2005",
        "show": 32.72, "ch_off": 131.99, "mgain": 1.0,
        "tag": "花田里犯了错",
        "note": "京剧与流行真正咬在一起，中国风的第一块拼图",
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
    mseek = q(max(0, item["ch_off"] - full_start_local))  # 源时间码：footage+音频同 seek = 口型同步
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
sys.path.insert(0, str(ROOT.parents[1]))  # ROOT.parents[1] = repo root，让 tools 可 import
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


def cut_footage(src_clip, seek, length, out_name):
    """输出端 seek 切竖屏 footage 段（口型对齐用，准确）。已存在且未 FORCE_CLIPS 则跳过（mgain 调音重建免重切）。"""
    if (CS / out_name).exists() and not os.environ.get("FORCE_CLIPS"):
        return
    run([
        "ffmpeg", "-v", "error", "-i", str(C / f"{src_clip}.mp4"), "-ss", str(seek), "-t", str(length),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / out_name), "-y",
    ])


segments = []

if not HTML_ONLY:
    # ---- intro: 伯牙绝弦动态封面 footage + 花田错床 + 旁白 ----
    cut_footage(INTRO_FOOT_CLIP, INTRO_SEEK, intro_end, "intro.mp4")
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
    if not HTML_ONLY:
        # COUPLED：footage 段从源 mseek 输出端 seek 切（与音频同基准 → 口型同步）
        cut_footage(block["clip"], block["mseek"], block["seg_dur"], f"{block['key']}.mp4")
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
    cut_footage(OUTRO_FOOT_CLIP, OUTRO_SEEK, outro_dur, "outro.mp4")
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
    # 单条 footage_track（硬规则：多 <video> 会让 HF 帧0 协议超时；拼成 1 条只挂 1 个 video）
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
        ("05", "伯牙绝弦"),
        ("04", "竹林深处"),
        ("03", "心中的日月"),
        ("02", "在梅边"),
        ("01", "花田错"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0c0a07;
  font-family:"PingFang SC",system-ui,sans-serif;color:#f2ece0;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0c0a07}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(12,10,7,.90),rgba(12,10,7,.04) 30%,rgba(12,10,7,.16) 55%,rgba(8,6,4,.95))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.42;background:radial-gradient(42% 26% at 18% 16%,rgba(220,180,96,.34),rgba(220,180,96,0) 65%),radial-gradient(48% 30% at 82% 84%,rgba(190,70,46,.22),rgba(190,70,46,0) 68%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.05;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(242,236,224,.13) 0 1px,rgba(242,236,224,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(224,196,120,0),rgba(224,196,120,.5),rgba(190,90,50,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:128px 76px 120px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(10,8,5,.84),rgba(10,8,5,.10) 32%,rgba(10,8,5,.22) 60%,rgba(8,6,4,.92))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:29px;font-weight:900;color:#e0c074;letter-spacing:.12em}
.eyebrow:before{content:"";width:56px;height:4px;background:#e0c074;border-radius:99px;box-shadow:0 0 18px rgba(224,192,116,.6)}
#cover h1{margin-top:28px;font-family:"Songti SC",serif;font-size:118px;line-height:1.08;font-weight:900;letter-spacing:.02em;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.74)}
#cover h1 b{color:#edcf8a;font-weight:900}
#cover h1 .sm{display:block;font-size:70px;margin-top:8px;color:#f2ece0}
#cover .sub{margin-top:540px;font-size:34px;line-height:1.52;color:#e4dcc9;font-weight:600;max-width:912px;text-shadow:0 3px 20px rgba(0,0,0,.82)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(224,192,116,.5);color:#f0e6cf;background:rgba(10,8,5,.55);font-size:26px;font-weight:800;padding:11px 18px;border-radius:7px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:178px;padding:34px 38px 38px;background:linear-gradient(135deg,rgba(10,8,5,.92),rgba(34,24,14,.56));border-left:8px solid #c79a4e;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.4)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e0c074;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:27px;font-weight:700;color:#b8a98f;letter-spacing:.05em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:82px;line-height:1.1;font-weight:900;color:#f6f0e4}
.fullLabel .tag{margin-top:19px;font-size:41px;line-height:1.26;font-weight:900;color:#edcf8a}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#e4dcc9}
.fullLabel.topRank{border-left-color:#d8482f;background:linear-gradient(135deg,rgba(28,12,8,.93),rgba(10,8,5,.6))}
.fullLabel.topRank .rank{color:#f3b24a}
.fullLabel.topRank .tag{color:#f6c060}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(10,8,5,.7);border:1.5px solid rgba(224,192,116,.5);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#f6f0e4;background:#0c0a07;border:1px solid rgba(224,192,116,.5);border-radius:6px;padding:2px 9px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:37px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(216,72,47,.78)}
.miniLabel.topRank span{border-color:rgba(243,178,74,.72)}
#outro{position:absolute;z-index:5;inset:0;padding:108px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(10,8,5,.42),rgba(10,8,5,.9))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e0c074;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:55px;line-height:1.3;font-weight:900;max-width:936px}
#outro ol{margin-top:34px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 22px;background:rgba(10,8,5,.64);border:1px solid rgba(242,236,224,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#f6f0e4;background:#0c0a07;border:1px solid rgba(224,192,116,.46);border-radius:6px;padding:4px 9px;line-height:1.1;min-width:60px;text-align:center}
#outro li:last-child{background:rgba(216,72,47,.16);border-color:rgba(216,72,47,.46)}
#outro li:last-child span{border-color:rgba(243,178,74,.66)}
#outro li strong{font-family:"Songti SC",serif;font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:28px;font-size:30px;line-height:1.5;color:#e4dcc9;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:96px;text-align:center;padding:22px;background:rgba(10,8,5,.72);border:1.5px solid rgba(243,178,74,.44);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f6c060;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#e0c074;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语中国风 · CHINKED-OUT 开创者</div>'
    '<h1>王力宏<span class="sm">最<b>中国风</b>的5首歌</span></h1></div>'
    '<div><p class="sub">二十年前，他把京剧、昆曲，和各地的民族音乐，写进了流行歌里。这五首，是王力宏最中国风、也最见野心的作品。</p>'
    '<div class="chips" style="margin-top:26px"><span>京剧昆曲</span><span>民族采风</span><span>说唱古典</span><span>Chinked-out</span><span>越听越有味</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>从京剧到昆曲，从藏地的吟唱到草原的辽阔，王力宏把中国风，唱成了能稳稳站住脚的一种声音。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这五首，就是他写给中国风，最漂亮的一份答卷。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.02,duration:3.4,ease:"sine.inOut",yoyo:true,repeat:1}},0.25);
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
    "id": "main", "name": "wanglihong-zhongguofeng-top5", "sample": SAMPLE,
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
