#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 罗志祥最难的5首歌."""
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

TITLE = "罗志祥最难的5首歌"
SLUG = "luozhixiang-hardest-top5"

LEAD = 0.3
POST = 0.2
DIG = 1.6
BED = 0.14
VOICE_GAIN = 2.0
INTRO_END = 22.0
INTRO_VOICE = 1.2
COVER_END = 6.4
INTRO_CLIP = "vert_bujuming"        # 片头底片 = 第一首出场歌《不具名的悲伤》动态画面（罗志祥正脸特写）
INTRO_MEDIA_START = 200.0           # 罗志祥演唱特写正脸（封面用，与 #5 同源）
CTA_GAP = 1.0
OUTRO_TAIL = 2.5
# 暗调/安静歌补偿（副歌响度对齐 ~-15dB）
MGAIN = {"p5_bujuming": 1.12, "p4_pinshenme": 1.12, "p3_duyiwuer": 1.06}

SONGS = [
    {
        "key": "p5_bujuming",
        "clip": "vert_bujuming",
        "no": "05",
        "name": "《不具名的悲伤》",
        "plain": "不具名的悲伤",
        "year": "2012 · 有我在",
        "cred": "词 管启源 · 曲 林倛玉",
        "show_start": 192.0,
        "show": 26.0,
        "tag": "站着唱，也糊弄不过去",
        "note": "五分钟的慢歌耐力战，把说不出名字的悲伤，一点点堆上去。",
    },
    {
        "key": "p4_pinshenme",
        "clip": "vert_pinshenme",
        "no": "04",
        "name": "《拼什么》",
        "plain": "拼什么",
        "year": "2011 · 独一无二",
        "cred": "词 姚若龙 · 曲 徐继宗",
        "show_start": 138.0,
        "show": 24.0,
        "tag": "他第一次拿慢歌打头阵",
        "note": "前面要稳、要真，后面要爆发，又不能唱成硬挤。",
    },
    {
        "key": "p3_duyiwuer",
        "clip": "vert_duyiwuer",
        "no": "03",
        "name": "《独一无二》",
        "plain": "独一无二",
        "year": "2011 · 独一无二",
        "cred": "词 陈镇川 · 曲 Evan Bogart 等",
        "show_start": 75.0,
        "show": 22.0,
        "tag": "电子舞曲里的稳与狠",
        "note": "要有态度、有律动，声音还不能被编曲吞掉。",
    },
    {
        "key": "p2_wujixian",
        "clip": "vert_wujixian",
        "no": "02",
        "name": "《舞极限》",
        "plain": "舞极限",
        "year": "2012 · 舞极限",
        "cred": "词 严云农 · 曲 H. Kovalainen 等",
        "show_start": 156.0,
        "show": 26.0,
        "tag": "舞台歌手的完整能力",
        "note": "持续的律动加现场体能，副歌要炸，但不能喊散。",
    },
    {
        "key": "p1_jingwumen",
        "clip": "vert_jingwumen",
        "no": "01",
        "name": "《精舞门》",
        "plain": "精舞门",
        "year": "2006 · Speshow",
        "cred": "词 陈镇川 · 曲 Daniel Bedingfield",
        "show_start": 190.5,
        "show": 26.2,
        "tag": "唱跳难度的天花板",
        "note": "唱、跳、节奏、体能，必须同时在线。",
    },
]

RANKING_ROWS = [
    ("01", "精舞门"),
    ("02", "舞极限"),
    ("03", "独一无二"),
    ("04", "拼什么"),
    ("05", "不具名的悲伤"),
]

OUTRO_KEY = SONGS[-1]["key"]   # 片尾底片/床 = 压轴《精舞门》

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
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + POST + DIG)
    end = q(t + seg_len)
    media_seek = q(item["show_start"] - (LEAD + item["voice_dur"] + POST + DIG))
    blocks.append({**item, "start": q(t), "end": end, "seg_len": seg_len, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start, "media_seek": max(0.0, media_seek), "mseek": max(0.0, media_seek)})
    t = end

# 展示段对齐闸门（机械化强制）
sys.path.insert(0, str(ROOT.parents[1]))
try:
    from tools.video import showcase_align
    showcase_align.gate(blocks, ROOT / "probe" / "vocal_analysis.json",
                        consts=dict(POST=POST, DIG=DIG), plan_path=ROOT / "probe" / "showcase_plan.json")
except FileNotFoundError:
    print("[align] vocal_analysis.json not found yet — skipping gate (run vocal_segments first)")

outro_start = q(t)
cta_local = q(LEAD + d_outro + CTA_GAP)
outro_len = q(cta_local + d_cta + OUTRO_TAIL)
total = q(outro_start + outro_len)

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
            "ffmpeg", "-v", "error", "-ss", str(b["media_seek"]), "-i", f"{CLIPS}/{b['clip']}.mp4",
            "-t", str(b["seg_len"]), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-g", "30", "-keyint_min", "30", "-c:a", "aac", "-b:a", "192k",
            f"{CLIPS_SEG}/{b['key']}.mp4", "-y",
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
        out = f"seg_{b['key']}.wav"
        run([
            "ffmpeg", "-v", "error",
            "-i", f"{CLIPS_SEG}/{b['key']}.mp4",
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
        "-i", f"{CLIPS_SEG}/{OUTRO_KEY}.mp4",
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
    footage.append((f"clips_seg/{OUTRO_KEY}", outro_start, outro_len))

videos = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{E(start)}" data-duration="{q(duration)}" data-track-index="{0 if i % 2 == 0 else 6}" src="{src}.mp4" muted playsinline></video>'
    for i, (src, start, duration) in enumerate(footage)
)

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
        f'<div class="rank"><span class="no">{b["no"]}</span><span class="lab">最难 TOP 5</span></div>'
        f'<h2>{b["name"]}</h2><p class="yr">{b["year"]}</p><p class="cred">{b["cred"]}</p>'
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
        f'tl.from("#{fid} .yr",{{y:16,opacity:0,duration:.42,ease:"power2.out"}},{E(label_start + 0.66)});',
        f'tl.from("#{fid} .cred",{{y:14,opacity:0,duration:.42,ease:"power2.out"}},{E(label_start + 0.82)});',
        f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{E(label_start + 1.0)});',
        f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{E(label_start + 1.22)});',
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
  <div class="kicker">罗志祥 · 唱跳难度盘点</div>
  <h1>罗志祥<br><em>最难的</em>5首歌</h1>
  <p>他不是不会唱，是要边跳到缺氧，边把声音稳稳唱住。</p>
</section>
<section id="hook" class="clip" data-start="7.0" data-duration="6.4" data-track-index="4">
  <div class="hookK">先说结论</div>
  <div class="hookT">舞王的难，<br>从来不只是跳。</div>
</section>
<section id="bridge" class="clip" data-start="15.3" data-duration="5.8" data-track-index="5">
  <small>从第五名到第一名</small>
  <strong>一首比一首狠</strong>
</section>
"""
    intro_tweens = [
        'tl.set("#cover",{opacity:1},0);',
        'tl.set("#cover .kicker,#cover h1,#cover p",{opacity:1},0);',
        'tl.from("#cover .kicker",{y:-14,duration:.55,ease:"power2.out"},.08);',
        'tl.from("#cover h1",{scale:.985,y:18,duration:.8,ease:"power3.out"},.12);',
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
  <h2>快歌拼体能，<br>慢歌拼真功夫。</h2>
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
html,body{width:1080px;height:1920px;overflow:hidden;background:#06080d;color:#f3efe8;font-family:sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#06080d}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(4,7,13,.82),rgba(4,7,13,.06) 30%,rgba(4,7,13,.16) 56%,rgba(4,7,13,.90))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(122% 78% at 50% 42%,rgba(0,0,0,0) 45%,rgba(0,0,0,.60) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.07;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;z-index:8;inset:0;padding:172px 76px 0;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;text-align:center}
.kicker{font-size:30px;font-weight:800;letter-spacing:.20em;color:#4fd6f5;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#cover h1{margin-top:24px;font-family:serif;font-size:140px;line-height:1.02;font-weight:900;text-shadow:0 8px 42px rgba(0,0,0,.74)}
#cover h1 em{font-style:normal;color:#4fd6f5}
#cover p{margin-top:28px;max-width:880px;font-size:38px;line-height:1.45;font-weight:550;color:#dbe2ec;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#hook{position:absolute;z-index:5;left:76px;right:76px;top:312px}
.hookK{font-size:31px;font-weight:800;letter-spacing:.18em;color:#4fd6f5}
.hookK:before{content:"";display:inline-block;width:54px;height:3px;background:#4fd6f5;border-radius:3px;margin-right:18px;vertical-align:middle}
.hookT{margin-top:34px;font-family:serif;font-size:80px;line-height:1.26;font-weight:800;color:#f4f1ea}
#bridge{position:absolute;z-index:5;left:76px;right:76px;top:50%;transform:translateY(-50%);text-align:center}
#bridge small{display:block;font-size:40px;font-weight:800;letter-spacing:.24em;color:#aebccf;margin-bottom:24px}
#bridge strong{display:block;font-family:serif;font-size:108px;line-height:1.08;color:#4fd6f5;text-shadow:0 8px 44px rgba(0,0,0,.55)}
.labelFull{position:absolute;z-index:5;left:70px;right:70px;bottom:182px;padding:34px 40px 40px;background:linear-gradient(135deg,rgba(6,10,18,.88),rgba(6,10,18,.42));border-left:7px solid #4fd6f5;border-radius:8px;backdrop-filter:blur(3px)}
.labelFull .rank{display:flex;align-items:flex-end;gap:20px}
.labelFull .no{font-size:122px;line-height:.82;font-weight:900;color:#bdeeff;font-family:sans-serif}
.labelFull .lab{font-size:30px;font-weight:800;letter-spacing:.18em;color:#aebccf;padding-bottom:14px}
.labelFull h2{font-family:serif;margin-top:16px;font-size:84px;line-height:1.05;font-weight:900;color:#fff}
.labelFull .yr{margin-top:12px;font-size:27px;font-weight:600;letter-spacing:.04em;color:#9fb2c8}
.labelFull .cred{margin-top:8px;font-size:26px;font-weight:500;letter-spacing:.02em;color:#9fb2c8}
.labelFull .tag{margin-top:18px;font-size:42px;line-height:1.24;font-weight:850;color:#4fd6f5}
.labelFull .note{margin-top:14px;font-size:32px;line-height:1.42;font-weight:520;color:#d6dce6}
.labelFull.topRank{border-left-color:#ffd27a}
.labelFull.topRank .no,.labelFull.topRank .tag{color:#ffd27a}
.labelMini{position:absolute;z-index:5;top:96px;left:60px;display:flex;align-items:center;gap:16px;padding:12px 22px;background:rgba(6,10,18,.66);border:1px solid rgba(79,214,245,.55);border-radius:999px}
.labelMini span{font-size:42px;font-weight:900;color:#4fd6f5}
.labelMini strong{font-family:serif;font-size:38px;font-weight:850;color:#fff}
.labelMini.topRank{border-color:rgba(255,210,122,.72)}
.labelMini.topRank span{color:#ffd27a}
#outro{position:absolute;z-index:9;inset:0;padding:126px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;letter-spacing:.20em;color:#4fd6f5}
#outro h2{font-family:serif;margin-top:20px;font-size:74px;line-height:1.16;font-weight:850;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 28px;background:rgba(6,10,18,.64);border:1px solid rgba(255,255,255,.12);border-radius:9px}
#outro li span{font-size:34px;font-weight:900;color:#4fd6f5}
#outro li strong{font-family:serif;font-size:40px;font-weight:850;color:#fff}
#outro li.gold{border-color:rgba(255,210,122,.58);background:rgba(46,38,18,.55)}
#outro li.gold span{color:#ffd27a}
#ctaBar{position:absolute;z-index:10;left:60px;right:60px;bottom:118px;padding:34px 40px 38px;text-align:center;background:linear-gradient(135deg,rgba(79,214,245,.20),rgba(6,10,18,.90));border:1px solid rgba(79,214,245,.62);border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar div{font-size:48px;line-height:1.22;font-weight:900;color:#fff}
#ctaBar p{margin-top:20px;font-size:36px;font-weight:850;letter-spacing:.12em;color:#bdeeff}
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
