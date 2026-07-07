#!/usr/bin/env python3
"""Build master.wav + single footage_track.mp4 + HyperFrames HTML for 飞轮海最被低估的5首歌.

Single-footage-track approach (one <video> element) for render reliability — all footage
segments are concatenated into one continuous footage_track.mp4 aligned to the timeline.
"""
import contextlib
import json
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

TITLE = "飞轮海最被低估的5首歌"
SLUG = "feilunhai-underrated-top5"

LEAD = 0.3
POST = 0.2
DIG = 1.6
BED = 0.14
VOICE_GAIN = 2.0
INTRO_END = 22.0
INTRO_VOICE = 1.2
COVER_END = 6.4
INTRO_CLIP = "vert_p2_xiaxue"     # 片头底片：夏雪 MV 四人同框 (t=120 四人白衣同框)
INTRO_MEDIA_START = 120.0
OUTRO_MEDIA_START = 275.0         # 片尾底片/床：一个人流浪 finale 副歌 (与展示段 65-99 不同段)
CTA_GAP = 1.0
OUTRO_TAIL = 2.5
# 各源响度补偿（副歌对齐 ~-15dB）；p5 为 270p MV、p3 为 4K 修复
MGAIN = {"p5_zuijiatingzhong": 1.4, "p1_yigerenliulang": 1.0}  # p5 270p MV 偏轻 +3dB

SONGS = [
    {
        "key": "p5_zuijiatingzhong", "clip": "vert_p5_zuijiatingzhong",
        "no": "05", "name": "《最佳听众》", "plain": "最佳听众", "year": "越来越爱 · 2009",
        "show_start": 57.0, "show": 36.24,
        "tag": "不在爱情中心，却一直在你身边",
        "note": "飞轮海最温柔的一面陪伴。",
    },
    {
        "key": "p4_xinliyoushu", "clip": "vert_p4_xinliyoushu",
        "no": "04", "name": "《心里有数》", "plain": "心里有数", "year": "双面飞轮海 · 2008",
        "show_start": 86.35, "show": 35.82,
        "tag": "话没说破，其实都知道",
        "note": "藏在主打背后的清醒情歌。",
    },
    {
        "key": "p3_liuxialai", "clip": "vert_p3_liuxialai",
        "no": "03", "name": "《留下来》", "plain": "留下来", "year": "越来越爱 · 2009",
        "show_start": 208.18, "show": 32.81,
        "tag": "想挽留，却说得很克制",
        "note": "五月天怪兽写下的遗珠。",
    },
    {
        "key": "p2_xiaxue", "clip": "vert_p2_xiaxue",
        "no": "02", "name": "《夏雪》", "plain": "夏雪", "year": "飞轮海 · 2006",
        "show_start": 202.91, "show": 30.97,
        "tag": "夏天里，心还在下雪",
        "note": "最容易被忽略的干净抒情。",
    },
    {
        "key": "p1_yigerenliulang", "clip": "vert_p1_yigerenliulang",
        "no": "01", "name": "《一个人流浪》", "plain": "一个人流浪", "year": "飞轮海 · 2006",
        "show_start": 65.38, "show": 33.94,
        "tag": "一个人离开后，慢慢消化孤单",
        "note": "偶像团之外，最耐听的飞轮海。",
    },
]

RANKING_ROWS = [
    ("01", "一个人流浪"),
    ("02", "夏雪"),
    ("03", "留下来"),
    ("04", "心里有数"),
    ("05", "最佳听众"),
]

OUTRO_KEY = SONGS[-1]["key"]   # 片尾底片/床 = 压轴《一个人流浪》

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
                   "narr_start": narr_start, "narr_end": narr_end,
                   "full_start": full_start, "mseek": max(0.0, media_seek)})
    t = end

outro_start = q(t)
cta_local = q(LEAD + d_outro + CTA_GAP)
outro_len = q(cta_local + d_cta + OUTRO_TAIL)
total = q(outro_start + outro_len)

# ---- 展示段对齐闸门（机械化强制）----
sys.path.insert(0, str(ROOT.parents[1]))
from tools.video import showcase_align
showcase_align.gate(blocks, ROOT / "probe" / "vocal_analysis.json",
                    consts=dict(POST=POST, DIG=DIG), plan_path=ROOT / "probe" / "showcase_plan.json")


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


# =========================== build footage segments ===========================
import os
outro_song = next(b for b in blocks if b["key"] == OUTRO_KEY)
SKIP_FOOTAGE = os.environ.get("SKIP_FOOTAGE") and (ROOT / "footage_track.mp4").exists()
if not SKIP_FOOTAGE:
    run([
        "ffmpeg", "-v", "error", "-ss", str(INTRO_MEDIA_START), "-i", f"{CLIPS}/{INTRO_CLIP}.mp4",
        "-t", str(INTRO_END), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", "-an", f"{CLIPS_SEG}/intro_clip.mp4", "-y",
    ])
    for b in blocks:
        run([
            "ffmpeg", "-v", "error", "-ss", str(b["mseek"]), "-i", f"{CLIPS}/{b['clip']}.mp4",
            "-t", str(b["seg_len"]), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-g", "30", "-keyint_min", "30", "-an", f"{CLIPS_SEG}/{b['key']}.mp4", "-y",
        ])
    # outro footage = OUTRO_KEY clip from OUTRO_MEDIA_START (finale 副歌段，与展示段不同)
    run([
        "ffmpeg", "-v", "error", "-ss", str(OUTRO_MEDIA_START), "-i", f"{CLIPS}/{outro_song['clip']}.mp4",
        "-t", str(outro_len), "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", "-an", f"{CLIPS_SEG}/outro_clip.mp4", "-y",
    ])
    # concat all footage into ONE track (re-encode for clean keyframes throughout)
    order = ["intro_clip"] + [b["key"] for b in blocks] + ["outro_clip"]
    (ROOT / "footage_list.txt").write_text("".join(f"file 'clips_seg/{k}.mp4'\n" for k in order), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "footage_list.txt",
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", "footage_track.mp4", "-y",
    ])

# =========================== build master.wav ===========================
segments = []
intro_env = (
    f"(lt(t,0.8))*(0.12*t/0.8)"
    f"+(between(t,0.8,{INTRO_VOICE+d_intro+0.8}))*0.12"
    f"+(between(t,{INTRO_VOICE+d_intro+0.8},{INTRO_END}))*(0.12+0.10*(t-{INTRO_VOICE+d_intro+0.8})/{max(0.5, INTRO_END-(INTRO_VOICE+d_intro+0.8))})"
)
run([
    "ffmpeg", "-v", "error",
    "-ss", str(INTRO_MEDIA_START), "-i", f"{CLIPS}/{INTRO_CLIP}.mp4",
    "-i", f"{AUDIO}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE*1000)}|{int(INTRO_VOICE*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{INTRO_END},loudnorm=I=-16:TP=-1.0:LRA=11,volume='{intro_env}':eval=frame[music];"
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
        "-ss", str(b["mseek"]), "-i", f"{CLIPS}/{b['clip']}.mp4",
        "-i", f"{AUDIO}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{b['seg_len']},loudnorm=I=-14:TP=-1.0:LRA=11,volume='{env}':eval=frame,volume={mgain}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['seg_len']},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

run([
    "ffmpeg", "-v", "error",
    "-ss", str(OUTRO_MEDIA_START), "-i", f"{CLIPS}/{outro_song['clip']}.mp4",
    "-i", f"{AUDIO}/outro.wav",
    "-i", f"{AUDIO}/cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)},volume={VOICE_GAIN}[vc];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{outro_len},loudnorm=I=-16:TP=-1.0:LRA=11,volume=0.20,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_len-1.6)}:d=1.6[music];"
    f"[vo][vc][music]amix=inputs=3:normalize=0:duration=longest,atrim=0:{outro_len},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
master_dur = dur(ROOT / "master.wav")
(ROOT / "build" / "timeline.json").write_text(json.dumps({"total": master_dur, "planned": total, "blocks": blocks}, ensure_ascii=False, indent=2), encoding="utf-8")
print("master dur:", master_dur, "/ planned:", total)

# =========================== build HTML ===========================
videos = f'<video id="fv" class="fv" data-start="0" data-duration="{total}" data-track-index="0" src="footage_track.mp4" muted playsinline></video>'

labels = []
tweens = []
for b in blocks:
    fid = f"lf{b['no']}"
    mid = f"lm{b['no']}"
    label_start = q(b["start"] + 0.25)
    label_dur = q(b["full_start"] - label_start)
    mini_dur = q(b["end"] - b["full_start"])
    top = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip labelFull{top}" data-start="{label_start}" data-duration="{label_dur}" data-track-index="2">'
        f'<div class="rank"><span class="no">{b["no"]}</span><span class="lab">最被低估 · TOP 5</span></div>'
        f'<h2>{b["name"]}</h2><p class="yr">{b["year"]}</p><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip labelMini{top}" data-start="{b["full_start"]}" data-duration="{mini_dur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.extend([
        f'tl.from("#{fid} .no",{{y:52,opacity:0,duration:.62,ease:"power3.out"}},{q(label_start + 0.06)});',
        f'tl.from("#{fid} .lab",{{x:-20,opacity:0,duration:.45,ease:"power2.out"}},{q(label_start + 0.28)});',
        f'tl.from("#{fid} h2",{{y:42,opacity:0,duration:.62,ease:"power3.out"}},{q(label_start + 0.38)});',
        f'tl.from("#{fid} .yr",{{y:16,opacity:0,duration:.42,ease:"power2.out"}},{q(label_start + 0.66)});',
        f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(label_start + 0.86)});',
        f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(label_start + 1.1)});',
        f'tl.to("#{fid}",{{opacity:0,duration:.38,ease:"power1.in"}},{q(b["full_start"] - 0.4)});',
        f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});',
        f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.48,ease:"power2.out"}},{q(b["full_start"] + 0.1)});',
        f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["end"] - 0.42)});',
        f'tl.set("#{mid}",{{opacity:0}},{q(b["end"])});',
    ])

intro_html = f"""
<section id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="8">
  <div class="kicker">飞轮海 · 遗珠盘点</div>
  <h1>飞轮海<br><em>最被低估</em>的5首歌</h1>
  <p>不是主打，不是热血合唱。<br>是被同张专辑盖过的，最温柔的飞轮海。</p>
</section>
<section id="hook" class="clip" data-start="7.0" data-duration="6.4" data-track-index="5">
  <div class="hookK">提起飞轮海</div>
  <div class="hookT">你记得主打歌，<br>却错过了他们最温柔的几首。</div>
</section>
<section id="bridge" class="clip" data-start="15.3" data-duration="5.8" data-track-index="6">
  <small>从第五名 到第一名</small>
  <strong>被盖过的温柔</strong>
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

rows = "".join(f'<li class="{"gold" if n == "01" else ""}" id="rr{n}"><span>{n}</span><strong>{name}</strong></li>' for n, name in RANKING_ROWS)
cta_start_abs = q(outro_start + cta_local)
outro_html = f"""
<section id="outro" class="clip" data-start="{q(outro_start + 0.3)}" data-duration="{q(outro_len - 0.3)}" data-track-index="9">
  <div class="small">完整榜单</div>
  <h2>被盖过的歌里，<br>藏着最深的飞轮海。</h2>
  <ol>{rows}</ol>
</section>
<section id="ctaBar" class="clip" data-start="{q(cta_start_abs - 0.35)}" data-duration="{q(total - cta_start_abs + 0.35)}" data-track-index="10">
  <div>你最想为哪一首投票？</div>
  <p>点赞 · 收藏 · 关注</p>
</section>
"""
outro_tweens = [
    f'tl.from("#outro .small",{{x:-22,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start + 0.7)});',
    f'tl.from("#outro h2",{{y:30,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start + 1.1)});',
    *[
        f'tl.from("#rr{n}",{{x:-30,opacity:0,duration:.48,ease:"power3.out"}},{q(outro_start + 5.6 + i * .72)});'
        for i, n in enumerate(["05", "04", "03", "02", "01"])
    ],
    f'tl.from("#ctaBar",{{y:30,opacity:0,duration:.55,ease:"power3.out"}},{q(cta_start_abs - 0.2)});',
]

audio_tag = f'<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

css = """
@font-face{font-family:'PingFang SC';src:local('PingFang SC')}
@font-face{font-family:'Songti SC';src:local('Songti SC')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0b0a0e;color:#f3ede2;font-family:"PingFang SC",sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0b0a0e}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,6,10,.80),rgba(8,6,10,.05) 28%,rgba(8,6,10,.14) 56%,rgba(8,6,10,.90))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(122% 78% at 50% 42%,rgba(0,0,0,0) 44%,rgba(0,0,0,.62) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.06;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;z-index:8;inset:0;padding:140px 70px 0;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;text-align:center}
.kicker{font-size:31px;font-weight:800;letter-spacing:.22em;color:#e8b87e;text-shadow:0 6px 24px rgba(0,0,0,.7)}
#cover h1{margin-top:26px;font-family:"Songti SC",serif;font-size:116px;line-height:1.12;font-weight:900;text-shadow:0 8px 42px rgba(0,0,0,.82)}
#cover h1 em{font-style:normal;color:#f1c98e}
#cover p{margin-top:30px;max-width:860px;font-size:37px;line-height:1.5;font-weight:550;color:#e6dccd;text-shadow:0 6px 24px rgba(0,0,0,.85)}
#hook{position:absolute;z-index:5;left:76px;right:76px;top:320px}
.hookK{font-size:31px;font-weight:800;letter-spacing:.20em;color:#e8b87e}
.hookK:before{content:"";display:inline-block;width:54px;height:3px;background:#e8b87e;border-radius:3px;margin-right:18px;vertical-align:middle}
.hookT{margin-top:34px;font-family:"Songti SC",serif;font-size:76px;line-height:1.3;font-weight:800;color:#f5efe4}
#bridge{position:absolute;z-index:5;left:76px;right:76px;top:50%;transform:translateY(-50%);text-align:center}
#bridge small{display:block;font-size:40px;font-weight:800;letter-spacing:.24em;color:#c7b9a6;margin-bottom:24px}
#bridge strong{display:block;font-family:"Songti SC",serif;font-size:102px;line-height:1.1;color:#f1c98e;text-shadow:0 8px 44px rgba(0,0,0,.55)}
.labelFull{position:absolute;z-index:5;left:70px;right:70px;bottom:188px;padding:34px 40px 40px;background:linear-gradient(135deg,rgba(14,10,16,.90),rgba(14,10,16,.46));border-left:7px solid #e8b87e;border-radius:9px;backdrop-filter:blur(3px)}
.labelFull .rank{display:flex;align-items:flex-end;gap:20px}
.labelFull .no{font-size:120px;line-height:.82;font-weight:900;color:#f1c98e;font-family:"PingFang SC",sans-serif}
.labelFull .lab{font-size:29px;font-weight:800;letter-spacing:.16em;color:#c7b9a6;padding-bottom:14px}
.labelFull h2{font-family:"Songti SC",serif;margin-top:16px;font-size:84px;line-height:1.05;font-weight:900;color:#fff}
.labelFull .yr{margin-top:12px;font-size:27px;font-weight:600;letter-spacing:.05em;color:#b3a591}
.labelFull .tag{margin-top:18px;font-size:42px;line-height:1.26;font-weight:850;color:#f1c98e}
.labelFull .note{margin-top:14px;font-size:32px;line-height:1.44;font-weight:520;color:#d9d0c2}
.labelFull.topRank{border-left-color:#ffcf8a}
.labelFull.topRank .no,.labelFull.topRank .tag{color:#ffcf8a}
.labelMini{position:absolute;z-index:5;top:96px;left:60px;display:flex;align-items:center;gap:16px;padding:12px 22px;background:rgba(14,10,16,.66);border:1px solid rgba(232,184,126,.55);border-radius:999px}
.labelMini span{font-size:42px;font-weight:900;color:#e8b87e}
.labelMini strong{font-family:"Songti SC",serif;font-size:38px;font-weight:850;color:#fff}
.labelMini.topRank{border-color:rgba(255,207,138,.72)}
.labelMini.topRank span{color:#ffcf8a}
#outro{position:absolute;z-index:9;inset:0;padding:120px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;letter-spacing:.20em;color:#e8b87e}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:70px;line-height:1.2;font-weight:850;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 28px;background:rgba(14,10,16,.64);border:1px solid rgba(255,255,255,.12);border-radius:9px}
#outro li span{font-size:34px;font-weight:900;color:#e8b87e}
#outro li strong{font-family:"Songti SC",serif;font-size:40px;font-weight:850;color:#fff}
#outro li.gold{border-color:rgba(255,207,138,.58);background:rgba(46,34,16,.55)}
#outro li.gold span{color:#ffcf8a}
#ctaBar{position:absolute;z-index:10;left:60px;right:60px;bottom:120px;padding:34px 40px 38px;text-align:center;background:linear-gradient(135deg,rgba(232,184,126,.20),rgba(14,10,16,.90));border:1px solid rgba(232,184,126,.62);border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.52)}
#ctaBar div{font-size:48px;line-height:1.22;font-weight:900;color:#fff}
#ctaBar p{margin-top:20px;font-size:36px;font-weight:850;letter-spacing:.14em;color:#f1d9b6}
"""

body = "\n".join([
    videos,
    f'<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>',
    f'<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="11"></div>',
    f'<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="12"></div>',
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
  <script src="vendor/gsap.min.js"></script>
  <style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
    {body}
  </div>
  <script>{js}</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("wrote index.html duration", total)
