#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML — 名侦探柯南主题曲影响力 TOP10.

倒数 10->1。展示段画面=《名侦探柯南》官方动画 OP/ED / 剧场版特报（柯南画面，无艺人 MV），
音频=干净录音室原曲（解耦，动画无口型）。日文歌名只作屏幕文字、不进配音。
最终音频以本脚本生成的 master.wav 后期 mux 为准（HyperFrames 会压平动态）。
"""
import contextlib
import json
import os
import subprocess
import wave
from pathlib import Path

HTML_ONLY = bool(os.environ.get("HTML_ONLY"))    # 只重生成 index.html，跳过 footage/audio 重切
AUDIO_ONLY = bool(os.environ.get("AUDIO_ONLY"))  # 只重建 master.wav（跳过 footage 重切）

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
RAW = ROOT / "raw"
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
# 副歌入声相对展示段起点的提前量（envelope: 展示段从 full_start_local 起音乐推满）


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def arun(cmd):
    """audio/master run — HTML_ONLY 模式下跳过（复用已有 wav）。"""
    if not HTML_ONLY:
        subprocess.run(cmd, cwd=ROOT, check=True)


def footage_path(stem):
    for ext in (".webm", ".mkv", ".mp4", ".m4v"):
        p = RAW / f"{stem}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(stem)


# 倒数顺序 10 -> 1（列表即展示先后）
items = [
    {"key": "p10", "no": "10", "jp": "TWILIGHT!!!", "artist": "King Gnu",
     "cat": "剧场版《独眼的残像》主题曲", "year": "2025",
     "foot": "fv10_twilight", "fseek": 33.0, "crop": "1920:1080:0:0",
     "aud": "au10_twilight", "ch_off": 60.3, "show": 40.0,
     "tag": "本榜最年轻的入选者", "note": "发行仅一年，先加一档新歌折扣"},
    {"key": "p9", "no": "09", "jp": "恋はスリル、ショック、サスペンス", "artist": "愛内里菜",
     "cat": "TV动画 第8首片头曲", "year": "2000",
     "foot": "fv09_koithrill", "fseek": 15.0, "crop": "1432:685:0:95",
     "aud": "au09_koithrill", "ch_off": 146.3, "show": 35.0,
     "tag": "柯南面无表情跳的帕拉帕拉", "note": "名场面与魔性生命力远超普通老片头"},
    {"key": "p8", "no": "08", "jp": "相思相愛", "artist": "aiko",
     "cat": "剧场版《百万美元的五棱星》主题曲", "year": "2024",
     "foot": "fv08_soushi", "fseek": 40.0, "crop": "1920:1080:0:0",
     "aud": "au08_soushi", "ch_off": 151.3, "show": 40.0,
     "tag": "新世代的播放强者", "note": "沉淀时间还短，暂未冲进前三"},
    {"key": "p7", "no": "07", "jp": "運命のルーレット廻して", "artist": "ZARD",
     "cat": "TV动画 第4首片头曲", "year": "1998",
     "foot": "fv07_unmei", "fseek": 15.0, "crop": "1432:685:0:95",
     "aud": "au07_unmei", "ch_off": 168.3, "show": 37.0,
     "tag": "最难从历史榜单里抹掉的一首", "note": "那把嗓音与早期柯南氛围焊死在一起"},
    {"key": "p6", "no": "06", "jp": "Time after time ～花舞う街で～", "artist": "倉木麻衣",
     "cat": "剧场版《迷宫的十字路》主题曲", "year": "2003",
     "foot": "fv06_timeafter", "fseek": 28.0, "crop": "626:360:0:0",
     "aud": "au06_timeafter", "ch_off": 136.3, "show": 34.0,
     "tag": "老剧场版党心里的白月光", "note": "京都·樱花·新一与小兰，情怀分高于算法分"},
    {"key": "p5", "no": "05", "jp": "クロノスタシス", "artist": "BUMP OF CHICKEN",
     "cat": "剧场版《万圣节的新娘》主题曲", "year": "2022",
     "foot": "fv05_chrono", "fseek": 120.0, "crop": "1920:1080:0:0",
     "aud": "au05_chrono", "ch_off": 185.3, "show": 38.0,
     "tag": "现代剧场版长尾最稳的一首", "note": "时间意象与警校组、佐藤高木线高度契合"},
    {"key": "p4", "no": "04", "jp": "謎", "artist": "小松未歩",
     "cat": "TV动画 第3首片头曲", "year": "1997",
     "foot": "fv04_nazo", "fseek": 18.0, "crop": "1432:685:0:95",
     "aud": "au04_nazo", "ch_off": 209.3, "show": 38.0,
     "tag": "最有柯南味的一首", "note": "前奏一响，五秒进入“今晚又要死人了”"},
    {"key": "p3", "no": "03", "jp": "Secret of my heart", "artist": "倉木麻衣",
     "cat": "TV动画 第9首片尾曲", "year": "2000",
     "foot": "bili_ed9_4k", "fseek": 30.0, "crop": "1920:730:0:140",
     "aud": "au03_secret", "ch_off": 138.3, "show": 40.0,
     "tag": "柯南片尾曲的第一张名片", "note": "二十多年播放依旧稳得吓人"},
    {"key": "p2", "no": "02", "jp": "渡月橋 ～君 想ふ～", "artist": "倉木麻衣",
     "cat": "剧场版《唐红的恋歌》主题曲", "year": "2017",
     "foot": "fv02_togetsukyo", "fseek": 16.0, "crop": "1920:1080:0:0",
     "aud": "au02_togetsukyo", "ch_off": 171.3, "show": 32.0,
     "tag": "剧场版综合口碑冠军", "note": "歌与电影共生的最好范本，差一点点就是第一"},
    {"key": "p1", "no": "01", "jp": "美しい鰭", "artist": "スピッツ",
     "cat": "剧场版《黑铁的鱼影》主题曲", "year": "2023",
     "foot": "fv01_utsukushii", "fseek": 88.0, "crop": "1920:1080:0:0",
     "aud": "au01_utsukushii", "ch_off": 192.3, "show": 34.0,
     "tag": "口碑与播放的双料冠军", "note": "真正跑成了一首国民级的长尾作品"},
]

# 响度补偿（QA 后微调）。au01(美しい鰭)改用 @196 响亮副歌窗后无需额外增益。
MGAIN = {}

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
    blocks.append({**it, "start": q(t), "end": end, "narr_start": narr_start,
                   "narr_end": narr_end, "full_start": full_start,
                   "full_start_local": full_start_local, "narr_end_local": narr_end_local,
                   "aud_start": aud_start, "seg_dur": seg_dur})
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


def make_footage(out_path, src, fseek, crop, length, br="-0.36", sat="1.05"):
    if HTML_ONLY or AUDIO_ONLY:
        return
    run([
        "ffmpeg", "-v", "error", "-i", str(src), "-ss", str(fseek), "-t", str(length),
        "-filter_complex",
        f"[0:v]crop={crop},split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=32,eq=brightness={br}:saturation={sat}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]",
        "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", str(out_path), "-y",
    ])


segments = []

# ---- INTRO ----
intro_foot = footage_path("fv05_chrono")
make_footage(CS / "intro.mp4", intro_foot, 30.0, "1920:1080:0:0", intro_end)
# intro 低音量床 = #1 录音室原曲（直接读 mp3）
arun([
    "ffmpeg", "-v", "error",
    "-ss", "62", "-i", str(RAW / "au01_utsukushii.mp3"),
    "-i", str(A / "intro.wav"),
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={q(intro_end-0.9)}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

# ---- SONG SEGMENTS ----
for b in blocks:
    src = footage_path(b["foot"])
    make_footage(CS / f"{b['key']}.mp4", src, b["fseek"], b["crop"], b["seg_dur"])
    env = envelope(b["narr_end_local"], b["full_start_local"])
    mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    arun([
        "ffmpeg", "-v", "error",
        "-ss", str(b["aud_start"]), "-i", str(RAW / f"{b['aud']}.mp3"),
        "-i", str(A / f"{b['key']}.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{b['seg_dur']},volume='{env}':eval=frame,volume={mg}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['seg_dur']},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

# ---- OUTRO ----
outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
outro_foot = footage_path("fv08_soushi")
make_footage(CS / "outro.mp4", outro_foot, 40.0, "1920:1080:0:0", outro_dur)
arun([
    "ffmpeg", "-v", "error",
    "-ss", "177", "-i", str(RAW / "au01_utsukushii.mp3"),  # #1 副歌做 outro 床（情绪收尾）
    "-i", str(A / "outro.wav"),
    "-i", str(A / "outro_cta.wav"),
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.17,afade=t=in:st=0:d=0.9,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
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

# 渲染占位静音轨（真音频后期 mux）：避免 HF 把 103MB master.wav base64 内联进单 HTML 导致 Chrome 超时
if not (ROOT / "silent.m4a").exists() or not HTML_ONLY:
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", str(total), "-c:a", "aac", "-b:a", "16k", str(ROOT / "silent.m4a"), "-y",
    ], cwd=ROOT, check=True)

# 单一 footage 轨：把 12 段 footage 按时间线顺序拼成一条连续视频，HTML 只挂 1 个 <video>。
# （12 个 <video> 会让 HF 在页面初始化时同时建 12 个 frame-player → Chrome 挂死/protocolTimeout）
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

def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
            f'data-track-index="{track}" src="{src}" muted playsinline></video>')


# 单一连续 footage 轨（见上 footage_track 拼接）：只挂 1 个 <video>，页面轻、渲染稳。
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
        f'<div class="cat">{b["cat"]} · {b["year"]}</div>'
        f'<h2 class="jp">{b["jp"]}</h2><div class="artist">{b["artist"]}</div>'
        f'<p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip mini{top}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["jp"]}</strong></section>'
    )
    s, fs, e = b["start"], b["full_start"], b["end"]
    tweens.append(f'tl.fromTo("#{fid} .rank",{{x:-30,opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power3.out"}},{q(s+.18)});')
    tweens.append(f'tl.fromTo("#{fid} .cat",{{x:-20,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"sine.out"}},{q(s+.38)});')
    tweens.append(f'tl.fromTo("#{fid} .jp",{{y:42,opacity:0}},{{y:0,opacity:1,duration:.62,ease:"power3.out"}},{q(s+.52)});')
    tweens.append(f'tl.fromTo("#{fid} .artist",{{y:20,opacity:0}},{{y:0,opacity:1,duration:.46,ease:"power1.out"}},{q(s+.78)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power1.out"}},{q(s+.98)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:16,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+1.22)});')
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
    f'<li{" class=top" if b["no"]=="01" else ""}><span>{b["no"]}</span><strong>{b["jp"]}</strong><em>{b["artist"]}</em></li>'
    for b in blocks
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:100 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
@font-face{font-family:"Hiragino Mincho ProN";src:local("Hiragino Mincho ProN");font-weight:300 900}
@font-face{font-family:"Hiragino Sans";src:local("Hiragino Sans");font-weight:300 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#05080f;
  font-family:"PingFang SC",system-ui,sans-serif;color:#f4f1ea;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#05080f}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(5,8,15,.86),rgba(5,8,15,.12) 30%,rgba(5,8,15,.30) 60%,rgba(3,4,9,.95))}
#vig{position:absolute;inset:0;z-index:1;box-shadow:inset 0 0 360px rgba(0,0,0,.78)}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.5;background:radial-gradient(40% 24% at 18% 16%,rgba(226,59,78,.42),rgba(226,59,78,0) 66%),radial-gradient(46% 30% at 82% 80%,rgba(96,139,176,.30),rgba(96,139,176,0) 70%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.07;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(244,241,234,.13) 0 1px,rgba(244,241,234,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(226,59,78,0),rgba(226,59,78,.62),rgba(96,139,176,0));transform-origin:center}

#cover{position:absolute;inset:0;z-index:5;padding:150px 76px 140px;display:flex;flex-direction:column;justify-content:space-between;
  background:linear-gradient(180deg,rgba(5,8,15,.78),rgba(5,8,15,.20) 32%,rgba(5,8,15,.24) 58%,rgba(3,4,9,.92))}
.brandline{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#e23b4e;letter-spacing:.34em}
.brandline:before{content:"";width:64px;height:4px;background:#e23b4e;border-radius:99px;box-shadow:0 0 20px rgba(226,59,78,.7)}
#cover h1{margin-top:30px;font-family:"Songti SC",serif;font-size:120px;line-height:1.08;font-weight:900;text-shadow:0 6px 44px rgba(0,0,0,.66)}
#cover h1 b{color:#e23b4e}
#cover .toptag{display:inline-block;margin-top:26px;font-family:"JetBrains Mono",monospace;font-size:46px;font-weight:900;color:#f4f1ea;
  letter-spacing:.16em;border:2px solid rgba(226,59,78,.6);border-radius:10px;padding:10px 26px;background:rgba(5,8,15,.5)}
#cover .sub{margin-top:30px;font-size:35px;line-height:1.5;color:#dfe5ef;font-weight:600;max-width:920px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:940px}
.chips span{border:1.5px solid rgba(96,139,176,.5);color:#e7eef7;background:rgba(5,8,15,.55);font-size:27px;font-weight:800;padding:11px 18px;border-radius:8px}

.card{position:absolute;z-index:5;left:60px;right:60px;bottom:172px;padding:34px 38px 40px;
  background:linear-gradient(135deg,rgba(7,10,18,.92),rgba(18,22,34,.62));border-left:9px solid #e23b4e;border-radius:8px;
  backdrop-filter:blur(3px);box-shadow:0 24px 74px rgba(0,0,0,.42)}
.card .rank{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:800;color:#e23b4e;letter-spacing:.18em}
.card .rank b{font-size:60px;font-weight:900;vertical-align:-6px;margin-left:4px}
.card .cat{margin-top:14px;font-size:29px;font-weight:700;color:#9fb2c6;letter-spacing:.04em}
.card .jp{font-family:"Hiragino Mincho ProN","Songti SC",serif;margin-top:12px;font-size:72px;line-height:1.14;font-weight:900;color:#f7f3ec}
.card .artist{margin-top:8px;font-size:38px;font-weight:800;color:#cdd8e6;letter-spacing:.06em}
.card .tag{margin-top:20px;font-size:39px;line-height:1.3;font-weight:900;color:#e23b4e}
.card .note{margin-top:11px;font-size:29px;line-height:1.44;font-weight:600;color:#dfe5ef}
.card.topRank{border-left-color:#ffce4d;background:linear-gradient(135deg,rgba(16,12,6,.94),rgba(7,10,18,.66))}
.card.topRank .rank,.card.topRank .tag{color:#ffce4d}

.mini{position:absolute;z-index:5;top:92px;left:56px;display:flex;align-items:center;gap:16px;padding:13px 22px;
  background:rgba(5,8,15,.72);border:1.5px solid rgba(226,59,78,.6);border-radius:9px}
.mini span{font-family:"JetBrains Mono",monospace;font-size:42px;font-weight:900;color:#f4f1ea;background:#05080f;border:1px solid rgba(226,59,78,.55);border-radius:6px;padding:2px 10px;line-height:1.1}
.mini strong{font-family:"Hiragino Mincho ProN","Songti SC",serif;font-size:34px;font-weight:900;max-width:800px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mini.topRank{border-color:rgba(255,206,77,.78)}
.mini.topRank span{border-color:rgba(255,206,77,.72);color:#ffce4d}

#outro{position:absolute;z-index:5;inset:0;padding:104px 64px 150px;display:flex;flex-direction:column;justify-content:center;
  background:linear-gradient(180deg,rgba(5,8,15,.40),rgba(3,4,9,.88))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e23b4e;letter-spacing:.2em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:56px;line-height:1.26;font-weight:900;max-width:940px}
#outro ol{margin-top:30px;list-style:none;display:grid;gap:9px;width:100%}
#outro li{display:flex;align-items:center;gap:18px;padding:12px 18px;background:rgba(7,10,18,.66);border:1px solid rgba(244,241,234,.12);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:900;color:#f4f1ea;background:#05080f;border:1px solid rgba(226,59,78,.45);border-radius:6px;padding:3px 9px;min-width:56px;text-align:center}
#outro li strong{font-family:"Hiragino Mincho ProN","Songti SC",serif;font-size:30px;font-weight:900;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#outro li em{font-style:normal;font-size:24px;font-weight:700;color:#9fb2c6}
#outro li.top{background:rgba(255,206,77,.14);border-color:rgba(255,206,77,.5)}
#outro li.top span{border-color:rgba(255,206,77,.65);color:#ffce4d}
#outro .close{margin-top:26px;font-size:30px;line-height:1.5;color:#dfe5ef;font-weight:600}

#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:96px;text-align:center;padding:22px;background:rgba(5,8,15,.74);border:1.5px solid rgba(255,206,77,.42);border-radius:10px}
#cta .v{font-size:44px;font-weight:900;color:#ffce4d;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#e23b4e;letter-spacing:.16em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="11"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="brandline">名侦探柯南 · 主题曲盘点</div>'
    '<h1>柯南主题曲<br>影响力 <b>TOP10</b></h1>'
    '<div class="toptag">10 → 1 倒数揭晓</div></div>'
    '<div><p class="sub">从口碑、传唱到长尾热度，三十年里最难被忘记的十段前奏。</p>'
    '<div class="chips"><span>剧场版主题曲</span><span>历代 OP / ED</span><span>国民级长尾</span><span>青春与回忆</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">FINAL RANKING</div>'
    '<h2>案子会忘，凶手会忘，<br>可那段前奏一响，时间就回来了。</h2>'
    f'<ol>{ranking_rows}</ol>'
    '<p class="close">十首主题曲，也是几代人关于柯南的青春切片。</p></section>'
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
    "id": "main", "name": "conan-theme-top10", "total": total,
    "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [{"no": b["no"], "jp": b["jp"], "start": b["start"], "full_start": b["full_start"],
                "end": b["end"], "aud_start": b["aud_start"], "ch_off": b["ch_off"],
                "seg_dur": b["seg_dur"]} for b in blocks],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
for b in blocks:
    print(b["no"], b["jp"][:14], "start", b["start"], "full", b["full_start"], "end", b["end"], "aud_start", b["aud_start"])
