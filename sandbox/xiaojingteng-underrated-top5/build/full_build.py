#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 萧敬腾最被低估的5首歌.

Countdown 5 -> 1 (#1 = 话不多 climax).
- #5 爸爸：官方MV（华纳官方频道，灰调棚band），COUPLED，裁底烧词。
- #4 我在哭：**DECOUPLED** —— 音频=录音室《我在哭》(raw/p4_aud.wav)，画面=同专辑(2008)《会痛的石头》官方MV B&W 特写。
- #3 活在故事里：**DECOUPLED** —— 音频改录音室版(raw/p3_aud.wav=cdsZkPQYSzA，原花莲 live 混音器乐占比过高)，画面仍用花莲 2013 live(裁 Julie 水印+烧入标题)。
- #2 白蛇传：官方MV（演唱会式，乐队+小提琴），COUPLED，裁底烧词。
- #1 话不多：**DECOUPLED** —— 原 8aMrEua 现场源音轨损坏(18s 后静音)，音频改用录音室《话不多》(raw/p1_aud.wav)，画面仍用 8aMrEua 现场。
事实口径：白蛇传/活在故事里/爸爸=本人词曲(可说"他写")；话不多(李焯雄/陈伟)、我在哭(邬裕康/李偲菘)非他创作。
专辑年份：狂想曲 2011 / 以爱之名 2012 / 同名专辑 2008。
封面=第一首出场(#5 爸爸)动态画面，intro footage 取 vert_p5_baba 连续窗流入 #5（删静态 cover_hero）。
Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> render intro + #5 + #1 + outro pilot. HTML_ONLY=1 -> skip audio rebuild.
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

INTRO_BED_AUD = "p5"      # 爸爸（封面/intro 底片同源）
OUTRO_BED_AUD = "p5"      # 爸爸（reflective 收尾床）
OUTRO_BED_SEEK = 170.0    # 爸爸 final chorus 做 swell
OUTRO_FOOT_SRC = "vert_p5_baba"
OUTRO_FOOT_SEEK = 66.0    # 爸爸 棚band 暖镜


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


ITEMS = [
    {
        "key": "p5_baba", "no": "05", "aud": "p5",
        "name": "《爸爸》", "plain": "爸爸", "meta": "以爱之名 · 2012",
        # 烧词地图确认连续在唱区 144-185（爸爸他只是個大朋友…因為他會一直守候…爸爸等待…等待 for you），
        # 186-208 是纯器乐 break（旧窗 186 起＝前半全器乐，用户反馈）→改用 147.7-185.8 全程在唱。
        "show": 38.1, "ch_off": 147.7, "mgain": 0.82,
        "tag": "写给爸爸，没说出口的那句",
        "note": "他自己写词写曲，私人、朴素、不讨巧",
    },
    {
        "key": "p4_zaiku", "no": "04", "aud": "p4",
        "name": "《我在哭》", "plain": "我在哭", "meta": "同名专辑 · 2008",
        # 旧 show=26.5 在乐句 gap 戛然而止 → 延到 163.5（含 146.7-162.7 整段唱完）解决"没唱完"。
        "show": 45.31, "ch_off": 118.17, "mgain": 0.91,
        "foot_seek": 114.0,   # 画面=《会痛的石头》MV（解耦，同专辑同年代 B&W），窗 114-180 避开 ~183 起的宽镜
        "tag": "把委屈，收着唱给你听",
        "note": "爆发力收住，情绪一点一点往下沉",
    },
    {
        "key": "p3_gushili", "no": "03", "aud": "p3",
        "name": "《活在故事里》", "plain": "活在故事里", "meta": "以爱之名 · 2012",
        # DECOUPLED：原花莲粉丝 live 混音器乐占比过高(用户反馈)→音频改录音室版(raw/p3_aud.wav=cdsZkPQYSzA)，
        # 画面仍用花莲 live(vert_p3_gushili)；人声更靠前、更密。
        "show": 35.4, "ch_off": 154.1, "mgain": 1.0,
        "foot_seek": 13.0,
        "tag": "我们都活在自己讲的故事里",
        "note": "他自己写的概念，孤独的戏剧感",
    },
    {
        "key": "p2_baishe", "no": "02", "aud": "p2",
        "name": "《白蛇传》", "plain": "白蛇传", "meta": "狂想曲 · 2011",
        "show": 38.0, "ch_off": 63.0, "mgain": 1.12,
        "tag": "他不是在唱歌，是在演一个角色",
        "note": "自己写的词曲，戏剧感、东方感、野心",
    },
    {
        "key": "p1_buaduo", "no": "01", "aud": "p1",
        "name": "《话不多》", "plain": "话不多", "meta": "狂想曲 · 2011",
        # DECOUPLED：原 8aMrEua 现场源音轨损坏(18s 后静音) → 音频用录音室《话不多》(raw/p1_aud.wav)，
        # 画面仍用 8aMrEua 现场(vert_p1_buaduo)；慢/中速歌口型微差不可察。
        "show": 31.0, "ch_off": 138.52, "mgain": 1.08,
        "foot_seek": 75.0,
        "tag": "越不说，越有后劲",
        "note": "不靠大嗓，把话全压在声音里",
    },
]

items = [ITEMS[0], ITEMS[4]] if SAMPLE else ITEMS

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
    mseek = q(max(0, item["ch_off"] - full_start_local))   # music slice start in raw/<aud>_aud.wav
    foot_seek = q(item["foot_seek"]) if "foot_seek" in item else mseek  # decoupled override
    block = {
        **item,
        "clip": f"vert_{item['key']}",
        "foot_src": item.get("foot_src", f"vert_{item['key']}"),
        "start": q(t), "end": end,
        "narr_start": narr_start, "narr_end": narr_end,
        "full_start": full_start, "full_start_local": full_start_local,
        "mseek": mseek, "foot_seek": foot_seek, "seg_dur": q(end - t),
    }
    blocks.append(block)
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)

# intro footage = vert_p5_baba 连续窗，末尾贴住 #5 的 footage 起点 → 封面丝滑流入 #5
P5_MSEEK = blocks[0]["foot_seek"]   # #5 是 items[0]
INTRO_FOOT_SRC = "vert_p5_baba"
INTRO_FOOT_SEEK = q(max(0, P5_MSEEK - intro_end))
INTRO_BED_SEEK = INTRO_FOOT_SEEK

# ---- 展示段对齐闸门（硬规则 (C)，违规不出 master）----
sys.path.insert(0, str(ROOT.parents[1]))
from tools.video import showcase_align  # noqa: E402
vraw = json.loads((ROOT / "probe" / "vocal_analysis.json").read_text(encoding="utf-8"))
vmap = {b["clip"]: vraw[f'{b["aud"]}_aud']["vocal_segments"] for b in blocks}
showcase_align.gate(blocks, vmap,
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
        "ffmpeg", "-v", "error", "-ss", str(INTRO_FOOT_SEEK), "-i", str(C / f"{INTRO_FOOT_SRC}.mp4"),
        "-t", str(intro_end),
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
            "ffmpeg", "-v", "error", "-ss", str(block["foot_seek"]), "-i", str(C / f"{block['foot_src']}.mp4"),
            "-t", str(block["seg_dur"]),
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
        "ffmpeg", "-v", "error", "-ss", str(OUTRO_FOOT_SEEK), "-i", str(C / f"{OUTRO_FOOT_SRC}.mp4"),
        "-t", str(outro_dur),
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
        ("05", "爸爸"),
        ("04", "我在哭"),
        ("03", "活在故事里"),
        ("02", "白蛇传"),
        ("01", "话不多"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0a0d;
  font-family:"PingFang SC",system-ui,sans-serif;color:#f1ebe3;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a0a0d}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(10,10,13,.92),rgba(10,10,13,.06) 30%,rgba(10,10,13,.20) 55%,rgba(6,6,9,.96))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.40;background:radial-gradient(42% 26% at 18% 16%,rgba(210,85,63,.34),rgba(210,85,63,0) 65%),radial-gradient(48% 30% at 82% 84%,rgba(96,118,150,.24),rgba(96,118,150,0) 68%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.06;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(241,235,227,.12) 0 1px,rgba(241,235,227,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(210,85,63,0),rgba(210,85,63,.52),rgba(96,118,150,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:120px 76px 116px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(10,10,13,.84),rgba(10,10,13,.12) 30%,rgba(10,10,13,.24) 60%,rgba(6,6,9,.93))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#e08a6c;letter-spacing:.10em}
.eyebrow:before{content:"";width:58px;height:4px;background:#d2553f;border-radius:99px;box-shadow:0 0 18px rgba(210,85,63,.62)}
#cover h1{margin-top:28px;font-family:"Songti SC",serif;font-size:104px;line-height:1.1;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.72)}
#cover h1 b{color:#e2664a;font-weight:900}
#cover .sub{margin-top:560px;font-size:35px;line-height:1.5;color:#e6ddd2;font-weight:600;max-width:920px;text-shadow:0 3px 20px rgba(0,0,0,.85)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(210,85,63,.50);color:#f0e6da;background:rgba(10,10,13,.56);font-size:27px;font-weight:800;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(10,10,13,.92),rgba(40,20,16,.56));border-left:8px solid #c8503c;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.42)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e08a6c;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#b9a896;letter-spacing:.06em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:80px;line-height:1.12;font-weight:900;color:#f1ebe3}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#e2664a}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#e6ddd2}
.fullLabel.topRank{border-left-color:#e2664a;background:linear-gradient(135deg,rgba(46,20,12,.93),rgba(10,10,13,.60))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f08a5f}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(10,10,13,.70);border:1.5px solid rgba(210,85,63,.50);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#f1ebe3;background:#0a0a0d;border:1px solid rgba(210,85,63,.48);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(226,102,74,.78)}
.miniLabel.topRank span{border-color:rgba(226,102,74,.72)}
#outro{position:absolute;z-index:5;inset:0;padding:110px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(10,10,13,.42),rgba(10,10,13,.92))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e08a6c;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:52px;line-height:1.32;font-weight:900;max-width:936px}
#outro ol{margin-top:34px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(10,10,13,.64);border:1px solid rgba(241,235,227,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#f1ebe3;background:#0a0a0d;border:1px solid rgba(210,85,63,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(226,102,74,.15);border-color:rgba(226,102,74,.46)}
#outro li:last-child span{border-color:rgba(226,102,74,.66)}
#outro li strong{font-family:"Songti SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:28px;font-size:30px;line-height:1.5;color:#e6ddd2;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px;background:rgba(10,10,13,.74);border:1.5px solid rgba(226,102,74,.44);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f08a5f;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#e08a6c;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 不只是飙高音的雨神</div><h1>萧敬腾<br><b>最被低估</b>的5首歌</h1></div>'
    '<div><p class="sub">飙高音、炸全场之外，他还有更收、更细、更会讲故事的一面。这五首遗珠，藏着你可能从没认真听过的萧敬腾。</p>'
    '<div class="chips" style="margin-top:26px"><span>收着唱</span><span>戏剧感</span><span>故事感</span><span>自己写的</span><span>越听越深</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>萧敬腾从来不只是那个会飙高音、会炸场的雨神，他更是一个会收、会演、会讲故事的歌者。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这些被大热歌盖住的遗珠，刚好补全了他最克制、也最细腻的另一面。</p></section>'
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
    "id": "main", "name": "xiaojingteng-underrated-top5", "sample": SAMPLE,
    "total": total, "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "aud": b["aud"], "start": b["start"], "narr_start": b["narr_start"],
         "narr_end": b["narr_end"], "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "foot_seek": b["foot_seek"], "foot_src": b["foot_src"],
         "ch_off": b["ch_off"], "show": b["show"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start, "SAMPLE:", SAMPLE)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"], "foot", b["foot_seek"]) for b in blocks])
