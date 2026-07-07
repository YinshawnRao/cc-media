#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 陈粒最难唱的5首歌."""
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
(ROOT / "probe").mkdir(exist_ok=True)

TITLE = "陈粒最难唱的5首歌"
SLUG = "chenli-hardest-top5"

LEAD = 0.3
POST = 0.2
DIG = 1.6
BED = 0.14
VOICE_GAIN = 2.0
INTRO_END = 21.0
INTRO_VOICE = 1.2
COVER_END = 6.2
INTRO_CLIP = "vert_xiaoban"        # 片头底片/封面：小半 B&W 近景（清晰人脸，区别于各展示段）
INTRO_MEDIA_START = 60.0
CTA_GAP = 1.0
OUTRO_TAIL = 2.5
# 暗调/安静源补偿（副歌响度对齐 ~-15dB）
MGAIN = {"p4_xiaoban": 1.1, "p3_guang": 1.06, "p5_qiaodou": 1.12, "p2_zouma": 1.2}

# show_start = 该首副歌"音量推满"起点在 vert clip 源时间码（= showcase_align plan 的 ch_off）
# show       = 展示段时长；二者由 showcase_align.py plan 反推，勿手拍
SONGS = [
    {
        "key": "p5_qiaodou", "clip": "vert_qiaodou", "no": "05",
        "name": "《桥豆麻袋》", "plain": "桥豆麻袋", "year": "2016 · 小梦大半",
        "show_start": 109.75, "show": 30.07,
        "tag": "怪得自然，才是真功夫",
        "note": "越像在闹着玩，越容易翻车。",
    },
    {
        "key": "p4_xiaoban", "clip": "vert_xiaoban", "no": "04",
        "name": "《小半》", "plain": "小半", "year": "2016 · 小梦大半",
        "show_start": 192.65, "show": 24.0,
        "tag": "情绪一直悬着，最难",
        "note": "用力多一分，那点心事就散了。",
    },
    {
        "key": "p3_guang", "clip": "vert_guang", "no": "03",
        "name": "《光》", "plain": "光", "year": "2015 · 如也",
        "show_start": 113.19, "show": 29.88,
        "tag": "声音要轻，但不能虚",
        "note": "唱过了，就丢了那股清冷。",
    },
    {
        "key": "p2_zouma", "clip": "vert_zouma", "no": "02",
        "name": "《走马》", "plain": "走马", "year": "2015 · 如也",
        "show_start": 49.66, "show": 27.72,
        "tag": "松弛里，还藏着锋利",
        "note": "太平像念词，太满没了那口气。",
    },
    {
        "key": "p1_yiran", "clip": "vert_yiran", "no": "01",
        "name": "《易燃易爆炸》", "plain": "易燃易爆炸", "year": "2015 · 如也",
        "show_start": 110.19, "show": 34.43,
        "tag": "先冷到极致，再突然炸开",
        "note": "前面没气场，后面一炸就散。",
    },
]

RANKING_ROWS = [
    ("01", "易燃易爆炸"),
    ("02", "走马"),
    ("03", "光"),
    ("04", "小半"),
    ("05", "桥豆麻袋"),
]

OUTRO_KEY = SONGS[-1]["key"]   # 片尾底片/床 = 压轴《易燃易爆炸》

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
    blocks.append({**item, "start": q(t), "end": end, "seg_len": seg_len,
                   "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start,
                   "media_seek": max(0.0, media_seek), "mseek": max(0.0, media_seek)})
    t = end

# 🔒 展示段对齐闸门（违规不出 master）
sys.path.insert(0, str(ROOT.parents[1]))
from tools.video import showcase_align
showcase_align.gate(blocks, ROOT / "probe" / "vocal_analysis.json",
                    consts=dict(POST=POST, DIG=DIG),
                    plan_path=ROOT / "build" / "showcase_plan.json")

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
    (ROOT / "build" / "timeline.json").write_text(json.dumps({"total": master_dur, "blocks": blocks}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("master dur:", master_dur, "/ planned:", total)

    # 片尾底片：截压轴《易燃易爆炸》seg 的前 outro_len 秒
    run([
        "ffmpeg", "-v", "error", "-ss", "0", "-i", f"{CLIPS_SEG}/{OUTRO_KEY}.mp4",
        "-t", str(outro_len), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", "-an", f"{CLIPS_SEG}/outro_clip.mp4", "-y",
    ])
    # 单条 footage_track：按时间线 concat（HF 多 <video> 帧0挂死 → 拼单轨挂 1 个 video）
    ftparts = ["intro_clip"] + [b["key"] for b in blocks] + ["outro_clip"]
    (CLIPS_SEG / "ftlist.txt").write_text("".join(f"file '{p}.mp4'\n" for p in ftparts), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{CLIPS_SEG}/ftlist.txt",
         "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
         "-an", f"{CLIPS_SEG}/footage_track.mp4", "-y"])
    print("footage_track built")

videos = (
    f'<video id="fv" class="fv" data-start="0" data-duration="{part_duration}" '
    f'data-track-index="0" src="clips_seg/footage_track.mp4" muted playsinline></video>'
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
        f'<div class="rank"><span class="no">{b["no"]}</span><span class="lab">最难唱 TOP 5</span></div>'
        f'<h2>{b["name"]}</h2><p class="yr">{b["year"]}</p><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
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
        f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{E(label_start + 0.86)});',
        f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{E(label_start + 1.1)});',
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
  <div class="kicker">陈粒 · 唱功盘点</div>
  <h1>陈粒<br><em>最难唱的</em>5首歌</h1>
  <p>听着随性，唱起来全是坑。气息、咬字、收和放，每一样都在考功底。</p>
</section>
<section id="hook" class="clip" data-start="6.8" data-duration="6.2" data-track-index="4">
  <div class="hookK">先别急着跟唱</div>
  <div class="hookT">陈粒的歌，<br>看着简单，全是暗坑。</div>
</section>
<section id="bridge" class="clip" data-start="14.6" data-duration="5.6" data-track-index="5">
  <small>从第五名到第一名</small>
  <strong>越随性，越难唱</strong>
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
        'tl.from("#hook .hookK",{x:-24,opacity:0,duration:.48,ease:"power2.out"},6.9);',
        'tl.from("#hook .hookT",{y:26,opacity:0,duration:.62,ease:"power3.out"},7.25);',
        'tl.to("#hook",{opacity:0,duration:.4,ease:"power1.in"},12.6);',
        'tl.set("#hook",{opacity:0},13.0);',
        'tl.from("#bridge small",{y:14,opacity:0,duration:.42,ease:"power2.out"},14.75);',
        'tl.from("#bridge strong",{scale:.86,opacity:0,duration:.62,ease:"back.out(1.5)"},15.02);',
        'tl.to("#bridge",{opacity:0,duration:.45,ease:"power1.in"},19.9);',
        'tl.set("#bridge",{opacity:0},20.4);',
    ]

outro_html = ""
outro_tweens = []
if include_outro:
    rows = "".join(f'<li class="{"gold" if n == "01" else ""}" id="rr{n}"><span>{n}</span><strong>{name}</strong></li>' for n, name in RANKING_ROWS)
    cta_start_abs = q(outro_start + cta_local)
    outro_html = f"""
<section id="outro" class="clip" data-start="{E(outro_start + 0.3)}" data-duration="{q(outro_len - 0.3)}" data-track-index="9">
  <div class="small">完整榜单</div>
  <h2>唱得像不费劲，<br>才是最难的本事。</h2>
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
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0710;color:#f4efe6;font-family:sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a0710}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,5,12,.82),rgba(8,5,12,.05) 30%,rgba(8,5,12,.14) 56%,rgba(8,5,12,.90))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(122% 78% at 50% 42%,rgba(0,0,0,0) 45%,rgba(0,0,0,.60) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.07;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;z-index:8;inset:0;padding:172px 76px 0;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;text-align:center}
.kicker{font-size:30px;font-weight:800;letter-spacing:.20em;color:#eab58a;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#cover h1{margin-top:24px;font-family:serif;font-size:140px;line-height:1.02;font-weight:900;text-shadow:0 8px 42px rgba(0,0,0,.74)}
#cover h1 em{font-style:normal;color:#e89a64}
#cover p{margin-top:28px;max-width:880px;font-size:38px;line-height:1.45;font-weight:550;color:#e3dbcf;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#hook{position:absolute;z-index:5;left:76px;right:76px;top:312px}
.hookK{font-size:31px;font-weight:800;letter-spacing:.18em;color:#eab58a}
.hookK:before{content:"";display:inline-block;width:54px;height:3px;background:#eab58a;border-radius:3px;margin-right:18px;vertical-align:middle}
.hookT{margin-top:34px;font-family:serif;font-size:78px;line-height:1.28;font-weight:800;color:#f6f1e8}
#bridge{position:absolute;z-index:5;left:76px;right:76px;top:50%;transform:translateY(-50%);text-align:center}
#bridge small{display:block;font-size:40px;font-weight:800;letter-spacing:.24em;color:#cbb39c;margin-bottom:24px}
#bridge strong{display:block;font-family:serif;font-size:104px;line-height:1.08;color:#e89a64;text-shadow:0 8px 44px rgba(0,0,0,.55)}
.labelFull{position:absolute;z-index:5;left:70px;right:70px;bottom:188px;padding:34px 40px 40px;background:linear-gradient(135deg,rgba(14,9,18,.88),rgba(14,9,18,.42));border-left:7px solid #e89a64;border-radius:8px;backdrop-filter:blur(3px)}
.labelFull .rank{display:flex;align-items:flex-end;gap:20px}
.labelFull .no{font-size:122px;line-height:.82;font-weight:900;color:#f0c79e;font-family:sans-serif}
.labelFull .lab{font-size:30px;font-weight:800;letter-spacing:.18em;color:#c9b29c;padding-bottom:14px}
.labelFull h2{font-family:serif;margin-top:16px;font-size:84px;line-height:1.05;font-weight:900;color:#fff}
.labelFull .yr{margin-top:12px;font-size:27px;font-weight:600;letter-spacing:.04em;color:#bfa78f}
.labelFull .tag{margin-top:18px;font-size:42px;line-height:1.24;font-weight:850;color:#e89a64}
.labelFull .note{margin-top:14px;font-size:32px;line-height:1.42;font-weight:520;color:#dcd3c6}
.labelFull.topRank{border-left-color:#ffce6f}
.labelFull.topRank .no,.labelFull.topRank .tag{color:#ffce6f}
.labelMini{position:absolute;z-index:5;top:96px;left:60px;display:flex;align-items:center;gap:16px;padding:12px 22px;background:rgba(14,9,18,.66);border:1px solid rgba(232,154,100,.55);border-radius:999px}
.labelMini span{font-size:42px;font-weight:900;color:#eab58a}
.labelMini strong{font-family:serif;font-size:38px;font-weight:850;color:#fff}
.labelMini.topRank{border-color:rgba(255,206,111,.72)}
.labelMini.topRank span{color:#ffce6f}
#outro{position:absolute;z-index:9;inset:0;padding:126px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;letter-spacing:.20em;color:#eab58a}
#outro h2{font-family:serif;margin-top:20px;font-size:68px;line-height:1.18;font-weight:850;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 28px;background:rgba(14,9,18,.64);border:1px solid rgba(255,255,255,.12);border-radius:9px}
#outro li span{font-size:34px;font-weight:900;color:#eab58a}
#outro li strong{font-family:serif;font-size:40px;font-weight:850;color:#fff}
#outro li.gold{border-color:rgba(255,206,111,.58);background:rgba(46,34,16,.55)}
#outro li.gold span{color:#ffce6f}
#ctaBar{position:absolute;z-index:10;left:60px;right:60px;bottom:118px;padding:34px 40px 38px;text-align:center;background:linear-gradient(135deg,rgba(232,154,100,.20),rgba(14,9,18,.90));border:1px solid rgba(232,154,100,.62);border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar div{font-size:48px;line-height:1.22;font-weight:900;color:#fff}
#ctaBar p{margin-top:20px;font-size:36px;font-weight:850;letter-spacing:.12em;color:#f0c79e}
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
