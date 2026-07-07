#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 刘欢最难的5首歌."""
import contextlib
import json
import os
import subprocess
import wave
from pathlib import Path


def dur(wav):
    with contextlib.closing(wave.open(str(wav), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
CLIPS = ROOT / "clips"
CLIPS_SEG = ROOT / "clips_seg"
CLIPS_SEG.mkdir(exist_ok=True)

TITLE = "刘欢最难的5首歌"
SLUG = "liuhuan-hardest-top5"

LEAD = 0.3
POST = 0.2
DIG = 1.6
BED = 0.13
VOICE_GAIN = 2.0
INTRO_END = 20.0
INTRO_VOICE = 1.0
COVER_END = 6.2
INTRO_CLIP = "vert_congtou_clean"
INTRO_MEDIA_START = 5.0
INTRO_MUSIC_CLIP = "vert_congtou_clean"
INTRO_MUSIC_SEEK = 47.42
CTA_GAP = 1.0
OUTRO_TAIL = 2.5
MGAIN = {
    "p4_haohange": 1.08,
    "p2_wanwan": 1.05,
}

SONGS = [
    {
        "key": "p5_congtou",
        "clip": "vert_congtou_clean",
        "no": "05",
        "name": "《从头再来》",
        "plain": "从头再来",
        "year": "1997前后 · 公益励志代表作",
        "show_start": 47.42,
        "show": 31.8,
        "tag": "最低处重新站起来，比高音更难",
        "note": "不能油，不能喊口号，要把重量唱得真。",
    },
    {
        "key": "p4_haohange",
        "clip": "vert_haohange_clean",
        "no": "04",
        "name": "《好汉歌》",
        "plain": "好汉歌",
        "year": "1998 · 电视剧《水浒传》主题歌",
        "show_start": 47.81,
        "show": 45.8,
        "tag": "豪气、民歌味、江湖气，一口气顶住",
        "note": "唱轻了没气势，唱重了就变成吼。",
    },
    {
        "key": "p3_qianwan",
        "clip": "vert_qianwan_clean",
        "no": "03",
        "name": "《千万次的问》",
        "plain": "千万次的问",
        "year": "《北京人在纽约》主题曲",
        "show_start": 124.74,
        "show": 42.2,
        "tag": "不是一个点高，是整首歌都在追问",
        "note": "持续高位、强情绪推进，还要保住层次。",
    },
    {
        "key": "p2_wanwan",
        "clip": "vert_wanwan_clean",
        "no": "02",
        "name": "《弯弯的月亮》",
        "plain": "弯弯的月亮",
        "year": "李海鹰词曲 · 刘欢演唱",
        "show_start": 172.90,
        "show": 30.7,
        "tag": "温柔最难，难在气息和留白",
        "note": "声音要厚，却不能压住乡愁。",
    },
    {
        "key": "p1_fenghuang",
        "clip": "vert_fenghuangyufei_clean",
        "no": "01",
        "name": "《凤凰于飞》",
        "plain": "凤凰于飞",
        "year": "《甄嬛传》主题曲",
        "show_start": 230.53,
        "show": 26.5,
        "tag": "古典审美、长线条气息、戏剧张力一起难",
        "note": "唱轻了没格局，唱重了又失去贵气。",
    },
]

RANKING_ROWS = [
    ("01", "凤凰于飞"),
    ("02", "弯弯的月亮"),
    ("03", "千万次的问"),
    ("04", "好汉歌"),
    ("05", "从头再来"),
]
OUTRO_KEY = SONGS[-1]["key"]

meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
d_intro = dur(AUDIO / "intro.wav")
d_outro = dur(AUDIO / "outro.wav")
d_cta = dur(AUDIO / "cta.wav")

blocks = []
t = INTRO_END
for item in SONGS:
    item["voice_dur"] = dur(AUDIO / f"{item['key']}.wav")
    item["narration"] = meta[item["key"]]["text"]
    seg_len = q(LEAD + item["voice_dur"] + POST + DIG + item["show"])
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + POST + DIG)
    end = q(t + seg_len)
    media_seek = max(0.0, q(item["show_start"] - (LEAD + item["voice_dur"] + POST + DIG)))
    blocks.append({
        **item,
        "start": q(t),
        "end": end,
        "seg_len": seg_len,
        "narr_start": narr_start,
        "narr_end": narr_end,
        "full_start": full_start,
        "media_seek": media_seek,
        "mseek": media_seek,
        "foot_clip": item["clip"],
        "foot_seek": media_seek,
    })
    t = end

outro_start = q(t)
cta_local = q(LEAD + d_outro + CTA_GAP)
outro_len = q(cta_local + d_cta + OUTRO_TAIL)
total = q(outro_start + outro_len)

PART = os.environ.get("LH_PART", "")
SPLIT = 3
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
    import sys
    sys.path.insert(0, str(ROOT.parents[1]))
    from tools.video import showcase_align

    showcase_align.gate(
        blocks,
        ROOT / "probe" / "vocal_analysis.json",
        consts=dict(POST=POST, DIG=DIG),
        plan_path=ROOT / "build" / "showcase_plan.json",
    )

    run([
        "ffmpeg", "-v", "error", "-ss", str(INTRO_MEDIA_START), "-i", f"{CLIPS}/{INTRO_CLIP}.mp4",
        "-t", str(INTRO_END), "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", f"{CLIPS_SEG}/intro_clip.mp4", "-y",
    ])
    for b in blocks:
        run([
            "ffmpeg", "-v", "error", "-ss", str(b["foot_seek"]), "-i", f"{CLIPS}/{b['foot_clip']}.mp4",
            "-t", str(b["seg_len"]), "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-g", "30", "-keyint_min", "30", f"{CLIPS_SEG}/{b['key']}.mp4", "-y",
        ])

    (ROOT / "audio_music").mkdir(exist_ok=True)
    for b in blocks:
        run([
            "ffmpeg", "-v", "error", "-ss", str(b["media_seek"]), "-i", f"{CLIPS}/{b['clip']}.mp4",
            "-t", str(b["seg_len"]), "-vn", "-ac", "2", "-ar", "48000",
            f"audio_music/{b['key']}.wav", "-y",
        ])
    run([
        "ffmpeg", "-v", "error", "-ss", str(INTRO_MUSIC_SEEK), "-i", f"{CLIPS}/{INTRO_MUSIC_CLIP}.mp4",
        "-t", str(INTRO_END), "-vn", "-ac", "2", "-ar", "48000", "audio_music/intro.wav", "-y",
    ])
    run([
        "ffmpeg", "-v", "error", "-ss", str(blocks[-1]["media_seek"]), "-i", f"{CLIPS}/{blocks[-1]['clip']}.mp4",
        "-t", str(outro_len), "-vn", "-ac", "2", "-ar", "48000", "audio_music/outro.wav", "-y",
    ])

    segments = []
    intro_env = (
        f"(lt(t,0.8))*(0.12*t/0.8)"
        f"+(between(t,0.8,{INTRO_VOICE + d_intro + 0.8}))*0.12"
        f"+(between(t,{INTRO_VOICE + d_intro + 0.8},{INTRO_END}))*(0.12+0.10*(t-{INTRO_VOICE + d_intro + 0.8})/{max(0.5, INTRO_END - (INTRO_VOICE + d_intro + 0.8))})"
    )
    run([
        "ffmpeg", "-v", "error", "-i", "audio_music/intro.wav", "-i", f"{AUDIO}/intro.wav",
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
        out = f"seg_{b['key']}.wav"
        run([
            "ffmpeg", "-v", "error", "-i", f"audio_music/{b['key']}.wav", "-i", f"{AUDIO}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{b['seg_len']},volume='{env}':eval=frame,volume={MGAIN.get(b['key'], 1.0)}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['seg_len']},alimiter=level=disabled:limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ])
        segments.append(out)

    run([
        "ffmpeg", "-v", "error", "-i", "audio_music/outro.wav", "-i", f"{AUDIO}/outro.wav", "-i", f"{AUDIO}/cta.wav",
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
    (ROOT / "build" / "timeline.json").write_text(json.dumps({
        "total": master_dur,
        "planned": total,
        "partA": blocks[SPLIT - 1]["end"],
        "partB": q(master_dur - blocks[SPLIT]["start"]),
        "split_at": blocks[SPLIT]["start"],
        "blocks": blocks,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
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
        f'<div class="rank"><span class="no">{b["no"]}</span><span class="lab">刘欢难唱 TOP 5</span></div>'
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
  <div class="kicker">刘欢 · 声压与气息盘点</div>
  <h1>刘欢<br><em>最难唱的</em>5首歌</h1>
  <p>不是谁嗓门大，谁就能唱。真正难的是厚度、气息、咬字和戏剧感一起成立。</p>
</section>
<section id="hook" class="clip" data-start="7.0" data-duration="5.6" data-track-index="4">
  <div class="hookK">先把标准说清楚</div>
  <div class="hookT">这不是高音榜，<br>是综合难度榜。</div>
</section>
<section id="bridge" class="clip" data-start="14.0" data-duration="5.0" data-track-index="5">
  <small>从第五名开始</small>
  <strong>越往前，越难稳住</strong>
</section>
"""
    intro_tweens = [
        'tl.from("#cover .kicker",{y:-14,opacity:0,duration:.55,ease:"power2.out"},.08);',
        'tl.from("#cover h1",{scale:.985,y:18,opacity:0,duration:.8,ease:"power3.out"},.12);',
        'tl.from("#cover p",{y:18,opacity:0,duration:.58,ease:"power2.out"},.5);',
        f'tl.to("#cover",{{opacity:0,duration:.8,ease:"power1.inOut"}},{COVER_END - .8});',
        'tl.from("#hook .hookK",{x:-24,opacity:0,duration:.48,ease:"power2.out"},7.1);',
        'tl.from("#hook .hookT",{y:26,opacity:0,duration:.62,ease:"power3.out"},7.45);',
        'tl.to("#hook",{opacity:0,duration:.4,ease:"power1.in"},12.1);',
        'tl.from("#bridge small",{y:14,opacity:0,duration:.42,ease:"power2.out"},14.15);',
        'tl.from("#bridge strong",{scale:.86,opacity:0,duration:.62,ease:"back.out(1.5)"},14.42);',
        'tl.to("#bridge",{opacity:0,duration:.45,ease:"power1.in"},18.55);',
    ]

outro_html = ""
outro_tweens = []
if include_outro:
    rows = "".join(
        f'<li class="{"gold" if n == "01" else ""}" id="rr{n}"><span>{n}</span><strong>{name}</strong></li>'
        for n, name in RANKING_ROWS
    )
    cta_start_abs = q(outro_start + cta_local)
    outro_html = f"""
<section id="outro" class="clip" data-start="{E(outro_start + 0.3)}" data-duration="{q(outro_len - 0.3)}" data-track-index="9">
  <div class="small">完整榜单</div>
  <h2>刘欢最难的地方，<br>是把厚重唱得有命运感。</h2>
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
html,body{width:1080px;height:1920px;overflow:hidden;background:#080607;color:#f6efe8;font-family:sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#080607}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,5,5,.86),rgba(8,5,5,.08) 32%,rgba(8,5,5,.16) 58%,rgba(8,5,5,.94))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 42%,rgba(0,0,0,0) 42%,rgba(0,0,0,.62) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.06;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;z-index:8;inset:0;padding:168px 76px 0;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;text-align:center}
.kicker{font-size:30px;font-weight:800;letter-spacing:.20em;color:#f1c37d;text-shadow:0 6px 24px rgba(0,0,0,.75)}
#cover h1{margin-top:24px;font-family:serif;font-size:140px;line-height:1.02;font-weight:900;text-shadow:0 8px 42px rgba(0,0,0,.74)}
#cover h1 em{font-style:normal;color:#d7a447}
#cover p{margin-top:28px;max-width:880px;font-size:38px;line-height:1.45;font-weight:550;color:#e8ddd0;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#hook{position:absolute;z-index:5;left:76px;right:76px;top:330px}
.hookK{font-size:31px;font-weight:800;letter-spacing:.18em;color:#f1c37d}
.hookK:before{content:"";display:inline-block;width:54px;height:3px;background:#d7a447;border-radius:3px;margin-right:18px;vertical-align:middle}
.hookT{margin-top:34px;font-family:serif;font-size:78px;line-height:1.28;font-weight:850;color:#f7f1ea}
#bridge{position:absolute;z-index:5;left:76px;right:76px;top:50%;transform:translateY(-50%);text-align:center}
#bridge small{display:block;font-size:40px;font-weight:800;letter-spacing:.24em;color:#d7b88c;margin-bottom:24px}
#bridge strong{display:block;font-family:serif;font-size:92px;line-height:1.08;color:#d7a447;text-shadow:0 8px 44px rgba(0,0,0,.55)}
.labelFull{position:absolute;z-index:5;left:70px;right:70px;bottom:176px;padding:34px 40px 40px;background:linear-gradient(135deg,rgba(12,8,7,.92),rgba(12,8,7,.46));border-left:7px solid #b9893f;border-radius:8px;backdrop-filter:blur(3px)}
.labelFull .rank{display:flex;align-items:flex-end;gap:20px}
.labelFull .no{font-size:122px;line-height:.82;font-weight:900;color:#d7a447;font-family:sans-serif}
.labelFull .lab{font-size:30px;font-weight:800;letter-spacing:.18em;color:#d7b88c;padding-bottom:14px}
.labelFull h2{font-family:serif;margin-top:16px;font-size:80px;line-height:1.05;font-weight:900;color:#fff}
.labelFull .yr{margin-top:12px;font-size:27px;font-weight:600;letter-spacing:.04em;color:#c5aa84}
.labelFull .tag{margin-top:18px;font-size:40px;line-height:1.24;font-weight:850;color:#e5b15b}
.labelFull .note{margin-top:14px;font-size:32px;line-height:1.42;font-weight:520;color:#e3dad2}
.labelFull.topRank{border-left-color:#ffe08c}
.labelFull.topRank .no,.labelFull.topRank .tag{color:#ffe08c}
.labelMini{position:absolute;z-index:5;top:96px;left:60px;display:flex;align-items:center;gap:16px;padding:12px 22px;background:rgba(12,8,7,.68);border:1px solid rgba(215,164,71,.60);border-radius:999px}
.labelMini span{font-size:42px;font-weight:900;color:#d7a447}
.labelMini strong{font-family:serif;font-size:38px;font-weight:850;color:#fff}
.labelMini.topRank{border-color:rgba(255,224,140,.72)}
.labelMini.topRank span{color:#ffe08c}
#outro{position:absolute;z-index:9;inset:0;padding:126px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;letter-spacing:.20em;color:#f1c37d}
#outro h2{font-family:serif;margin-top:20px;font-size:66px;line-height:1.18;font-weight:850;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 28px;background:rgba(12,8,7,.66);border:1px solid rgba(255,255,255,.12);border-radius:9px}
#outro li span{font-size:34px;font-weight:900;color:#d7a447}
#outro li strong{font-family:serif;font-size:40px;font-weight:850;color:#fff}
#outro li.gold{border-color:rgba(255,224,140,.58);background:rgba(46,34,16,.55)}
#outro li.gold span{color:#ffe08c}
#ctaBar{position:absolute;z-index:10;left:60px;right:60px;bottom:118px;padding:34px 40px 38px;text-align:center;background:linear-gradient(135deg,rgba(215,164,71,.22),rgba(12,8,7,.92));border:1px solid rgba(215,164,71,.62);border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar div{font-size:48px;line-height:1.22;font-weight:900;color:#fff}
#ctaBar p{margin-top:20px;font-size:36px;font-weight:850;letter-spacing:.12em;color:#f0d5a0}
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
