#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 伍佰最被低估的5首歌 (countdown 5->1).

Clips are pre-built by prep_clips.py: each clips/vert_<key>.mp4 already carries the
correct music audio (official MV audio for feiyu/zuile, studio recording for the three
montage救场 songs). So this build treats every song uniformly: [0:a] = clip music.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

# keep in sync with prep_clips.py
SHOW = 29.0
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {"p3_meiren": 1.38}  # 没人爱副歌段 loudnorm 后仍偏低 ~2.8dB，补偿到 ~-15.7dB
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
CTA_GAP = 1.0      # 消化位：作品 outro 念完到固定 CTA 之间
OUTRO_TAIL = 1.8   # CTA 念完留尾再 fade
INTRO_CLIP = "vert_p4_feiyu"      # atmospheric umbrella MV behind the cover
OUTRO_CLIP = "vert_p1_shouyinji"  # emotional closeup behind the ranking reveal


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

# countdown reveal order 5 -> 1
items = [
    {
        "key": "p5_laibuji", "clip": "vert_p5_laibuji", "no": "05",
        "name": "《来不及》", "plain": "来不及",
        "tag": "伍佰最厉害的，是后劲",
        "note": "被《浪人情歌》同名曲盖住的一句收尾",
    },
    {
        "key": "p4_feiyu", "clip": "vert_p4_feiyu", "no": "04",
        "name": "《飞在风中的小雨》", "plain": "飞在风中的小雨",
        "tag": "台语歌里少见的轻盈漂泊",
        "note": "硬汉伍佰，也写得出很软的孤独",
    },
    {
        "key": "p3_meiren", "clip": "vert_p3_meiren", "no": "03",
        "name": "《没人爱的女孩》", "plain": "没人爱的女孩",
        "tag": "最早的伍佰，最原始的拧巴",
        "note": "像一张越看越有故事的旧照片",
    },
    {
        "key": "p2_zuile", "clip": "vert_p2_zuile", "no": "02",
        "name": "《亲爱的，你喝醉了》", "plain": "亲爱的，你喝醉了",
        "tag": "粗粝又温柔的伍佰味",
        "note": "被《爱情的尽头》整张神专盖过的遗珠",
    },
    {
        "key": "p1_shouyinji", "clip": "vert_p1_shouyinji", "no": "01",
        "name": "《破碎的收音机》", "plain": "破碎的收音机",
        "tag": "夜里反复调频的那种空荡",
        "note": "真爱粉心里最舍不得的一首",
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "cta.wav")
for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + SHOW)
    b = {**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start}
    blocks.append(b)
    t = q(end + BETWEEN)

outro_start = q(t)
cta_start_local = q(LEAD + d_outro + CTA_GAP)   # CTA 旁白在 outro 段内的起点
total = q(outro_start + cta_start_local + d_cta + OUTRO_TAIL)


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

intro_dur = intro_end
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{INTRO_CLIP}.mp4",
        "-i", f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ]
)
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    run(
        [
            "ffmpeg", "-v", "error",
            "-i", f"{C}/{b['clip']}.mp4",
            "-i", f"{A}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(total - outro_start)
cta_delay = int(cta_start_local * 1000)
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{OUTRO_CLIP}.mp4",
        "-i", f"{A}/outro.wav",
        "-i", f"{A}/cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={cta_delay}|{cta_delay},volume={VOICE_GAIN}[vc];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.15,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-OUTRO_TAIL}:d={OUTRO_TAIL}[music];"
        f"[vo][vc][music]amix=inputs=3:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ]
)
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
planned_total = total
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)

# ---- realign visual timeline to ACTUAL segment durations (防音画累积漂移) ----
intro_end = dur(ROOT / "seg_intro.wav")
cur = intro_end
for b in blocks:
    pre_off = LEAD + b["voice_dur"] + 0.25 + DIG
    seg_actual = dur(ROOT / f"seg_{b['key']}.wav")
    b["start"] = q(cur)
    b["full_start"] = q(cur + pre_off)
    b["end"] = q(cur + seg_actual)
    cur = q(cur + seg_actual)
outro_start = q(cur)
assert abs(cur + dur(ROOT / "seg_outro.wav") - total) < 0.05, "timeline mismatch"


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, INTRO_CLIP)]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), OUTRO_CLIP))

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
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

# ranking 1 -> 5
ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("01", "破碎的收音机"), ("02", "亲爱的，你喝醉了"), ("03", "没人爱的女孩"),
        ("04", "飞在风中的小雨"), ("05", "来不及"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070a;font-family:"Noto Sans SC",sans-serif;color:#f6f1ea}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.74),rgba(0,0,0,.12) 34%,rgba(0,0,0,.20) 58%,rgba(0,0,0,.80))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.16) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:172px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;color:#e8b96a;letter-spacing:.06em}
.eyebrow:before{content:"";width:54px;height:4px;background:#e8b96a;border-radius:99px}
#cover h1{font-size:130px;line-height:1.03;font-weight:900;max-width:920px;text-wrap:balance;text-shadow:0 6px 40px rgba(0,0,0,.5)}
#cover .sub{margin-top:32px;font-size:39px;line-height:1.46;color:#ddd4c8;font-weight:600;max-width:860px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:880px}
.chips span{border:1px solid rgba(232,185,106,.5);color:#f3dcb0;background:rgba(12,10,14,.5);font-size:29px;font-weight:700;padding:12px 19px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:188px;padding:34px 36px 40px;background:linear-gradient(135deg,rgba(6,5,9,.82),rgba(6,5,9,.48));border-left:8px solid #e8b96a;border-radius:4px}
.fullLabel .rank{font-size:31px;font-weight:900;color:#e8b96a;letter-spacing:.04em}
.fullLabel h2{margin-top:14px;font-size:84px;line-height:1.06;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:43px;line-height:1.26;font-weight:800;color:#f2d49b}
.fullLabel .note{margin-top:13px;font-size:31px;line-height:1.4;font-weight:550;color:#cdc4b9}
.fullLabel.topRank{border-left-color:#ef4d5a}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff737d}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 19px;background:rgba(6,5,9,.68);border:1px solid rgba(232,185,106,.55);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:900;color:#e8b96a}
.miniLabel strong{font-size:38px;font-weight:800}
.miniLabel.topRank{border-color:rgba(239,77,90,.72)}
.miniLabel.topRank span{color:#ff737d}
#outro{position:absolute;z-index:5;inset:0;padding:138px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:33px;font-weight:800;color:#e8b96a;letter-spacing:.06em}
#outro h2{margin-top:18px;font-size:70px;line-height:1.14;font-weight:900;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 24px;background:rgba(6,5,9,.6);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:900;color:#e8b96a}
#outro li:first-child{border-color:rgba(239,77,90,.5)}
#outro li:first-child span{color:#ff737d}
#outro li strong{font-size:37px;font-weight:800}
#outro .close{margin-top:32px;font-size:33px;line-height:1.46;color:#ddd4c8;font-weight:600}
#ctaBar{position:absolute;z-index:6;left:60px;right:60px;bottom:118px;padding:36px 40px 40px;text-align:center;background:linear-gradient(135deg,rgba(232,185,106,.18),rgba(6,5,9,.86));border:1px solid rgba(232,185,106,.6);border-radius:16px;box-shadow:0 18px 60px rgba(0,0,0,.5)}
#ctaBar .q{font-size:48px;line-height:1.2;font-weight:900;color:#f6f1ea}
#ctaBar .q b{color:#e8b96a}
#ctaBar .acts{margin-top:22px;display:flex;justify-content:center;gap:30px;font-size:36px;font-weight:800;color:#f3dcb0}
#ctaBar .acts span{display:inline-flex;align-items:center;gap:8px}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">被低估的专辑遗珠</div><h1>伍佰最被低估的5首歌</h1>'
    '<p class="sub">在浪人情歌、挪威的森林这些大热之外，他还有几首被整张专辑光芒盖住的歌。越冷门，越是真爱粉的心头好。</p></div>'
    '<div class="chips"><span>专辑遗珠</span><span>越听越上头</span><span>被低估的温柔</span><span>真爱粉认证</span><span>后劲很大</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">完整榜单</div><h2>伍佰最被低估的，从来不是技术，是这些越听越久的温柔。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：来不及、飞在风中的小雨、没人爱的女孩、亲爱的你喝醉了、破碎的收音机。</p></section>'
)
cta_abs = q(outro_start + cta_start_local)
body += (
    f'\n<section id="ctaBar" class="clip" data-start="{q(cta_abs-0.3)}" data-duration="{q(total-cta_abs+0.3)}" data-track-index="5">'
    '<div class="q">你最想为哪一首<b>投票</b>？</div>'
    '<div class="acts"><span>♥ 点赞</span><span>★ 收藏</span><span>＋ 关注</span></div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# 封面首帧硬约束：t=0 即完整可作缩略图（不给封面元素 fade-in）；用轻微呼吸 + 背景footage运动提供动感
js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1,y:0}},0);
tl.to("#cover h1",{{scale:1.018,transformOrigin:"left center",duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},1.2);
tl.to("#cover .chips span",{{y:-4,duration:1.4,ease:"sine.inOut",stagger:.08,yoyo:true,repeat:1}},2.0);
tl.to("#cover",{{opacity:0,duration:.4,ease:"power1.in"}},{q(intro_end-.55)});
tl.set("#cover",{{opacity:0}},{q(intro_end-.1)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.25)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.6)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.25)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.15)});
tl.to("#outro .close",{{opacity:0,duration:.4,ease:"power1.in"}},{q(cta_abs-0.45)});
tl.set("#outro .close",{{opacity:0}},{q(cta_abs-0.05)});
tl.from("#ctaBar",{{y:34,opacity:0,duration:.5,ease:"power3.out"}},{q(cta_abs-0.3)});
tl.from("#ctaBar .acts span",{{y:14,opacity:0,duration:.4,ease:"power2.out",stagger:.09}},{q(cta_abs+0.25)});
tl.to("#ctaBar,#outro ol,#outro h2,#outro .small",{{opacity:0,duration:1.2,ease:"power1.in"}},{q(total-1.3)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@500;600;700;800;900&display=swap" rel="stylesheet" />
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "wubai-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
