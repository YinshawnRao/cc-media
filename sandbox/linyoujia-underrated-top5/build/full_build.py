#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 林宥嘉最被低估的5首歌 (countdown 5->1).

Female narration (zf_xiaoyi). Cover reveals no ranking; outro lists it; fixed CTA last.

Per-song music source is MIXED:
  - synced live (慢一点/飞): music = the clip's own live audio (footage==music window, lip-synced).
  - 蒙太奇救场 (耳朵/拾荒/4号病房): 官方无演唱 MV / 极冷门无干净现场 -> studio audio (黑胶/MV 音轨)
    aligned so its chorus (vocal-dense window, found via vocal_segments.py) lands on the showcase,
    over decoupled clean 本人特写 footage (a different concert). Slow songs -> 口型微差不可察.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 14.0
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0   # outro 升华 -> 固定 CTA 的消化位
CLIP_DUR = 34.0  # showcase clip length (footage must cover the whole block)

# per-song loudness compensation (tuned via volumedetect; tighten quiet outliers toward ~-15.5dB)
MGAIN = {"p2_manyidian": 1.18, "p4_sihao": 1.10, "p3_shihuang": 1.06}


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


# items in countdown order (5 -> 1).
# music: ("clip",) = use clip's own live audio (synced) ; ("wav", file, chorus_start) = studio montage
items = [
    {"key": "p5_fei", "clip": "vert_fei", "no": "05", "name": "《飞》", "plain": "飞",
     "album": "今日营业中", "tag": "往外走、往上飞的轻盈", "note": "不抓人，却在专辑后段慢慢发光",
     "music": ("sync", "raw/fei_foot.mp4")},
    {"key": "p4_sihao", "clip": "vert_sihao", "no": "04", "name": "《4号病房》", "plain": "4号病房",
     "album": "大小说家", "tag": "带情境、带角色的暗色戏", "note": "不只会唱心碎，也能唱一出小剧场",
     "music": ("wav", "raw/sihao_audio.wav", 193.0)},
    {"key": "p3_shihuang", "clip": "vert_shihuang", "no": "03", "name": "《拾荒》", "plain": "拾荒",
     "album": "大小说家", "tag": "用音乐说故事的收尾曲", "note": "在故事的废墟里，捡拾还值得相信的意义",
     "music": ("wav", "raw/shihuang_audio.wav", 216.0)},
    {"key": "p2_manyidian", "clip": "vert_manyidian", "no": "02", "name": "《慢一点》", "plain": "慢一点",
     "album": "神秘嘉宾", "tag": "求快时代里的悠闲散步", "note": "松弛、迷幻、慢半拍的早期 Yoga",
     "music": ("sync", "raw/manyidian_win.mp4")},
    {"key": "p1_erduo", "clip": "vert_erduo", "no": "01", "name": "《耳朵》", "plain": "耳朵",
     "album": "感官／世界", "tag": "听见了，却好像听不懂", "note": "不催泪，却把疏离唱得最细腻",
     "music": ("wav", "raw/erduo_audio.wav", 201.0)},
]

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
    full_start = q(narr_end + 0.25 + DIG)
    end = q(min(full_start + SHOW, t + CLIP_DUR - 0.15))   # clamp so footage never runs out
    b = {**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start}
    blocks.append(b)
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

# ---- intro: cover footage is silent -> narration over a low music bed (耳朵 studio) ----
intro_dur = intro_end
run([
    "ffmpeg", "-v", "error",
    "-ss", "20", "-i", "raw/erduo_audio.wav",
    "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},asetpts=N/SR/TB,volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

# ---- per-song segments ----
for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    env = song_envelope(narr_end_local, full_start_local)
    gain = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    mtype = b["music"][0]
    if mtype == "sync":
        # live audio from the raw window (frame-aligned with the clip, both from t=0)
        music_in = ["-i", b["music"][1]]
    else:
        _, wav, chorus_start = b["music"]
        seek = max(0.0, q(chorus_start - full_start_local))
        music_in = ["-ss", str(seek), "-i", wav]
    run([
        "ffmpeg", "-v", "error",
        *music_in,
        "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},asetpts=N/SR/TB,volume='{env}':eval=frame,volume={gain}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

# ---- outro (ranking reveal) + fixed CTA, over a chorus bed (耳朵 studio) ----
outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
run([
    "ffmpeg", "-v", "error",
    "-ss", "200", "-i", "raw/erduo_audio.wav",
    "-i", f"{A}/outro.wav",
    "-i", f"{A}/outro_cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},asetpts=N/SR/TB,volume=0.16,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
planned_total = total
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, "vert_cover")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_outro"))

labels = []
tweens = []
for idx, b in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    rank_class = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {b["no"]} 名</div><div class="albm">专辑 · {b["album"]}</div>'
        f'<h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["name"]}</strong></section>'
    )
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} .albm",{{y:18,opacity:0,duration:.4,ease:"power2.out"}},{q(b["start"]+.34)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.5)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.86)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+1.08)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong><em>{al}</em></li>'
    for n, name, al in [("01", "耳朵", "感官／世界"), ("02", "慢一点", "神秘嘉宾"),
                        ("03", "拾荒", "大小说家"), ("04", "4号病房", "大小说家"), ("05", "飞", "今日营业中")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#080910;font-family:"Noto Sans SC",sans-serif;color:#f1eff7}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#080910}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,7,16,.82),rgba(6,7,16,.10) 30%,rgba(6,7,16,.18) 56%,rgba(6,7,16,.86))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 78% at 50% 42%,transparent 52%,rgba(4,5,12,.66) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.09;background:repeating-linear-gradient(0deg,rgba(180,195,255,.16) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:158px 76px 146px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;color:#a6b6ec;letter-spacing:.08em}
.eyebrow:before{content:"";width:56px;height:4px;background:#a6b6ec;border-radius:99px}
#cover h1{font-family:"Noto Serif SC",serif;margin-top:30px;font-size:128px;line-height:1.04;font-weight:900;max-width:920px;text-wrap:balance;text-shadow:0 6px 42px rgba(0,0,0,.6)}
#cover h1 .hl{color:#a6b6ec}
#cover .sub{margin-top:30px;font-size:39px;line-height:1.5;color:#cfd2e6;font-weight:500;max-width:880px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(166,182,236,.5);color:#d6deff;background:rgba(10,12,22,.5);font-size:29px;font-weight:600;padding:12px 20px;border-radius:9px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:198px;padding:36px 38px 40px;background:linear-gradient(135deg,rgba(9,11,22,.84),rgba(9,11,22,.42));border-left:8px solid #a6b6ec;border-radius:5px;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:32px;font-weight:800;color:#a6b6ec;letter-spacing:.16em}
.fullLabel .albm{margin-top:10px;font-size:27px;font-weight:600;color:#9aa0bf;letter-spacing:.04em}
.fullLabel h2{font-family:"Noto Serif SC",serif;margin-top:14px;font-size:92px;line-height:1.04;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:43px;line-height:1.26;font-weight:700;color:#c2cdfb}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.42;font-weight:400;color:#c8c9da}
.fullLabel.topRank{border-left-color:#f0b35e}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f4c277}
.miniLabel{position:absolute;z-index:5;top:94px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 24px;background:rgba(9,11,22,.64);border:1px solid rgba(166,182,236,.55);border-radius:9px}
.miniLabel span{font-size:44px;font-weight:900;color:#a6b6ec}
.miniLabel strong{font-family:"Noto Serif SC",serif;font-size:40px;font-weight:800}
.miniLabel.topRank{border-color:rgba(240,179,94,.78)}
.miniLabel.topRank span{color:#f4c277}
#outro{position:absolute;z-index:5;inset:0;padding:140px 74px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:33px;font-weight:800;color:#a6b6ec;letter-spacing:.16em}
#outro h2{font-family:"Noto Serif SC",serif;margin-top:20px;font-size:66px;line-height:1.18;font-weight:900;max-width:940px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;gap:24px;padding:18px 26px;background:rgba(9,11,22,.6);border:1px solid rgba(200,210,255,.12);border-radius:10px}
#outro li span{font-size:36px;font-weight:900;color:#a6b6ec;min-width:60px}
#outro li strong{font-family:"Noto Serif SC",serif;font-size:44px;font-weight:800;flex:1}
#outro li em{font-style:normal;font-size:27px;font-weight:500;color:#9aa0bf}
#outro li:first-child{background:rgba(240,179,94,.12);border-color:rgba(240,179,94,.36)}
#outro li:first-child span{color:#f4c277}
#outro .close{margin-top:34px;font-size:32px;line-height:1.5;color:#cfd2e6;font-weight:500}
#cta{position:absolute;z-index:6;left:74px;right:74px;bottom:150px;text-align:center}
#cta .v{font-size:50px;font-weight:900;color:#f4c277;line-height:1.22}
#cta .f{margin-top:18px;font-size:36px;font-weight:800;color:#a6b6ec;letter-spacing:.12em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="8"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.45)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 唱作盘点</div>'
    '<h1>林宥嘉<span class="hl">最被低估</span>的5首歌</h1>'
    '<p class="sub">传唱度最高的那几首之外，这五首遗珠，藏着他最细腻、最讲究的样子。</p></div>'
    '<div class="chips"><span>细腻</span><span>疏离感</span><span>唱作</span><span>专辑遗珠</span><span>真爱粉向</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">完整榜单</div><h2>林宥嘉最迷人的，是慢慢渗进来的温柔。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：飞、4号病房、拾荒、慢一点、耳朵。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">你最想为哪一首投票？评论区告诉我</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
/* Cover must be COMPLETE at frame 0 (it is the thumbnail) -> no opacity fade-in. */
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.02,duration:3.0,ease:"sine.inOut",yoyo:true,repeat:1}},0.3);
tl.to("#cover",{{opacity:0,duration:.4,ease:"power1.in"}},{q(intro_end-.55)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
tl.set("#cta",{{opacity:1}},{q(cta_voice-0.2)});
tl.from("#cta .v",{{y:26,opacity:0,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.from("#cta .f",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(cta_voice+0.35)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Serif+SC:wght@500;700;900&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "linyoujia-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], q(b["end"]-b["start"])) for b in blocks])
