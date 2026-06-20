#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 戴佩妮最被低估的5首歌 (countdown 5->1).

Female narration (zf_xiaoyi). Cover reveals no ranking; outro lists it; fixed CTA last.

All five showcases use the STUDIO recording (extracted from each song's MV/source) as audio,
DECOUPLED from the closeup footage, with the chorus aligned onto the showcase window
(chorus_start found via vocal_segments.py). 水中央's footage window matches its studio time
so it is effectively lip-synced.

Footage diversification (year/show/outfit, per [diversify-footage-sources]):
  #5 非诚勿扰 2016 own neon-noir MV montage ; #4 转眼 ~2007 怎样 發現Live ;
  #3 安心睡着 2013 纯属意外音乐会 ; #2 钢琴键 2022 时光音乐会 ; #1 水中央 2003 DVD MV.
  cover/intro = 2016 钢琴键 MV frontal closeups ; outro = 2025 野薔薇.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
OUTRO_TAIL = 2.6
DIGEST_O = 1.0     # outro 升华 -> 固定 CTA 的消化位
INTRO_BED = "raw/shuizhongyang_studio.wav"   # low music bed for cover/intro & outro

# per-song loudness compensation (tuned via volumedetect; nudge quiet outliers toward ~-15.5dB)
MGAIN = {"p5_feicheng": 1.12, "p4_zhuanyan": 1.40, "p3_anxin": 1.0,
         "p2_gangqinjian": 1.05, "p1_shuizhongyang": 1.27}


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def vdur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return round(float(out), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


# items in countdown order (5 -> 1). music = ("wav", studio_wav, chorus_start); show = showcase seconds.
items = [
    {"key": "p5_feicheng", "clip": "vert_feicheng", "no": "05", "name": "《非诚勿扰》",
     "album": "专辑《贼》· 2016", "tag": "藏在后段的真爱粉私藏曲", "note": "不苦情，带着疏离，也带着清醒",
     "show": 18.0, "music": ("wav", "raw/feicheng_studio.wav", 145.0)},
    {"key": "p4_zhuanyan", "clip": "vert_zhuanyan", "no": "04", "name": "《转眼》",
     "album": "《No Penn, No Gain》· 2003", "tag": "写给老朋友的友情歌", "note": "把很轻的情绪，唱得一点都不轻浮",
     "show": 22.0, "music": ("wav", "raw/zhuanyan_studio.wav", 174.0)},
    {"key": "p3_anxin", "clip": "vert_anxin", "no": "03", "name": "《你怎么可以安心的睡着》", "longname": True,
     "album": "《纯属意外》· 2013", "tag": "英式摇滚的锋利", "note": "不是温柔的她，是带着质问与不甘的她",
     "show": 20.0, "music": ("wav", "raw/anxin_studio.wav", 130.0)},
    {"key": "p2_gangqinjian", "clip": "vert_gangqinjian", "no": "02", "name": "《钢琴键》",
     "album": "专辑《贼》· 2016", "tag": "最有电影感的一首", "note": "像手指慢慢按下，一颗一颗弹出旧伤",
     "show": 15.0, "music": ("wav", "raw/gangqinjian_studio.wav", 145.0)},
    {"key": "p1_shuizhongyang", "clip": "vert_shuizhongyang", "no": "01", "name": "《水中央》",
     "album": "《No Penn, No Gain》· 2003", "tag": "不写安全牌情歌的野心", "note": "异域感与水波感，越听越有画面",
     "show": 20.0, "music": ("wav", "raw/shuizhongyang_studio.wav", 139.5)},
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")
for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")
    item["clip_dur"] = vdur(C / f"{item['clip']}.mp4")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    # block end = full_start + show, clamped so footage never runs out
    end = q(min(full_start + item["show"], t + item["clip_dur"] - 0.15))
    b = {**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start}
    blocks.append(b)
    t = q(end)

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

# ---- intro: cover footage is silent -> narration over a low music bed (水中央 studio) ----
intro_dur = intro_end
run([
    "ffmpeg", "-v", "error",
    "-ss", "20", "-i", INTRO_BED,
    "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},asetpts=N/SR/TB,volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=level=disabled:limit=0.95[out]",
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
    _, wav, chorus_start = b["music"]
    seek = max(0.0, q(chorus_start - full_start_local))
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(seek), "-i", wav,
        "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},asetpts=N/SR/TB,volume='{env}':eval=frame,volume={gain}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

# ---- outro (ranking reveal) + fixed CTA, over a chorus bed (水中央 studio) ----
outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
run([
    "ffmpeg", "-v", "error",
    "-ss", "139", "-i", INTRO_BED,
    "-i", f"{A}/outro.wav",
    "-i", f"{A}/outro_cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},asetpts=N/SR/TB,volume=0.17,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
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
    name_class = "long" if b.get("longname") else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {b["no"]} 名</div><div class="albm">{b["album"]}</div>'
        f'<h2 class="{name_class}">{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
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
    for n, name, al in [("01", "水中央", "No Penn, No Gain"), ("02", "钢琴键", "贼"),
                        ("03", "你怎么可以安心的睡着", "纯属意外"), ("04", "转眼", "No Penn, No Gain"),
                        ("05", "非诚勿扰", "贼")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06100f;font-family:"Noto Sans SC",sans-serif;color:#eef4f2}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#06100f}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(4,12,12,.84),rgba(4,12,12,.08) 30%,rgba(4,12,12,.16) 56%,rgba(4,12,12,.88))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 78% at 50% 42%,transparent 52%,rgba(2,8,9,.66) 100%)}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.08;background:repeating-linear-gradient(0deg,rgba(150,230,220,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:158px 76px 146px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;color:#5fc9bf;letter-spacing:.1em}
.eyebrow:before{content:"";width:56px;height:4px;background:#5fc9bf;border-radius:99px}
#cover h1{font-family:"Noto Serif SC",serif;margin-top:30px;font-size:130px;line-height:1.04;font-weight:900;max-width:940px;text-wrap:balance;text-shadow:0 6px 42px rgba(0,0,0,.62)}
#cover h1 .hl{color:#6fd0c4}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.5;color:#cfe0dc;font-weight:500;max-width:900px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:920px}
.chips span{border:1px solid rgba(95,201,191,.5);color:#d4efea;background:rgba(8,18,18,.5);font-size:29px;font-weight:600;padding:12px 20px;border-radius:9px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:198px;padding:36px 40px 42px;background:linear-gradient(135deg,rgba(7,16,16,.86),rgba(7,16,16,.42));border-left:8px solid #5fc9bf;border-radius:6px;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:33px;font-weight:800;color:#5fc9bf;letter-spacing:.16em}
.fullLabel .albm{margin-top:10px;font-size:27px;font-weight:600;color:#93a7a3;letter-spacing:.03em}
.fullLabel h2{font-family:"Noto Serif SC",serif;margin-top:14px;font-size:90px;line-height:1.06;font-weight:900}
.fullLabel h2.long{font-size:60px;line-height:1.12}
.fullLabel .tag{margin-top:20px;font-size:43px;line-height:1.26;font-weight:700;color:#b6ece4}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.42;font-weight:400;color:#c5d2cf}
.fullLabel.topRank{border-left-color:#f0b35e}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f4c277}
.miniLabel{position:absolute;z-index:5;top:94px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 24px;background:rgba(7,16,16,.66);border:1px solid rgba(95,201,191,.55);border-radius:9px;max-width:900px}
.miniLabel span{font-size:44px;font-weight:900;color:#5fc9bf}
.miniLabel strong{font-family:"Noto Serif SC",serif;font-size:40px;font-weight:800}
.miniLabel.topRank{border-color:rgba(240,179,94,.78)}
.miniLabel.topRank span{color:#f4c277}
#outro{position:absolute;z-index:5;inset:0;padding:138px 74px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:33px;font-weight:800;color:#5fc9bf;letter-spacing:.16em}
#outro h2{font-family:"Noto Serif SC",serif;margin-top:20px;font-size:62px;line-height:1.2;font-weight:900;max-width:940px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;gap:22px;padding:17px 26px;background:rgba(7,16,16,.62);border:1px solid rgba(190,236,228,.12);border-radius:10px}
#outro li span{font-size:35px;font-weight:900;color:#5fc9bf;min-width:58px}
#outro li strong{font-family:"Noto Serif SC",serif;font-size:42px;font-weight:800;flex:1}
#outro li em{font-style:normal;font-size:25px;font-weight:500;color:#93a7a3}
#outro li:first-child{background:rgba(240,179,94,.12);border-color:rgba(240,179,94,.36)}
#outro li:first-child span{color:#f4c277}
#outro .close{margin-top:32px;font-size:31px;line-height:1.5;color:#cfe0dc;font-weight:500}
#cta{position:absolute;z-index:6;left:74px;right:74px;bottom:150px;text-align:center}
#cta .v{font-size:50px;font-weight:900;color:#f4c277;line-height:1.22}
#cta .f{margin-top:18px;font-size:36px;font-weight:800;color:#5fc9bf;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="vig" class="clip" data-start="0" data-duration="{total}" data-track-index="8"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 唱作盘点</div>'
    '<h1>戴佩妮<span class="hl">最被低估</span>的5首歌</h1>'
    '<p class="sub">传唱度最高的那几首之外，这五首遗珠，藏着她最诚实、最不讨好市场的样子。</p></div>'
    '<div class="chips"><span>诚实</span><span>唱作</span><span>专辑遗珠</span><span>越听越上头</span><span>真爱粉向</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">完整榜单</div><h2>戴佩妮最珍贵的，是那份不讨好市场的诚实。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：非诚勿扰、转眼、你怎么可以安心的睡着、钢琴键，和水中央。</p></section>'
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "daipeini-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["key"], b["start"], b["full_start"], b["end"], q(b["end"]-b["start"])) for b in blocks])
