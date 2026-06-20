#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Zhao Chuan (赵传) hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 28.0               # 展示段连续副歌（与 clips 的预切窗对齐：chorus 落在 full_start_local）
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {"p5_wochou": 1.18, "p4_gaoliang": 1.10, "p2_gei": 1.42}   # SMG暗调SD / 红高粱SD live / gei副歌偏轻 补偿
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0            # outro 升华 → 固定 CTA 的消化位（见 CONVENTIONS「固定结尾配音」）

INTRO_CLIP = "vert_wochou"     # 封面背景复用 #5（最先揭晓，无剧透）
OUTRO_CLIP = "vert_xiaoniao"   # 片尾复用 #1（压轴回望）


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


items = [
    {
        "key": "p5_wochou",
        "clip": "vert_wochou",
        "no": "05",
        "name": "《我很丑可是我很温柔》",
        "plain": "我很丑可是我很温柔",
        "tag": "撕裂的高音里，自嘲与脆弱并存",
        "note": "副歌要炸得开，还得同时唱出丑的自嘲和温柔的脆弱",
    },
    {
        "key": "p4_gaoliang",
        "clip": "vert_gaoliang",
        "no": "04",
        "name": "《红高粱》",
        "plain": "红高粱",
        "tag": "民歌腔、摇滚嗓、粗粝爆发一起上",
        "note": "要吼出土地的厚重和野性，不是单纯地用力喊",
    },
    {
        "key": "p3_aiyao",
        "clip": "vert_aiyao",
        "no": "03",
        "name": "《爱要怎么说出口》",
        "plain": "爱要怎么说出口",
        "tag": "副歌长句，气息与胸声的硬考验",
        "note": "喊上去之后，字头还要清楚、气不能散、情绪不能垮",
    },
    {
        "key": "p2_gei",
        "clip": "vert_gei",
        "no": "02",
        "name": "《给所有知道我名字的人》",
        "plain": "给所有知道我名字的人",
        "tag": "越唱越高、越唱越重，一路不能塌",
        "note": "把感恩、沧桑、倔强一层层推到结尾，尾段撑不住就垮",
    },
    {
        "key": "p1_xiaoniao",
        "clip": "vert_xiaoniao",
        "no": "01",
        "name": "《我是一只小小鸟》",
        "plain": "我是一只小小鸟",
        "tag": "持续高位、情绪爆发、巨大声压",
        "note": "唱的是卑微，拼的却是真功夫",
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")   # 固定引流 CTA（全片最后一句）
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
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)       # 升华后消化位 → 固定 CTA
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
cta_local = q(cta_voice - outro_start)   # CTA 在 outro 段内的起点
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{OUTRO_CLIP}.mp4",
        "-i", f"{A}/outro.wav",
        "-i", f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ]
)
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

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("01", "我是一只小小鸟"),
        ("02", "给所有知道我名字的人"),
        ("03", "爱要怎么说出口"),
        ("04", "红高粱"),
        ("05", "我很丑可是我很温柔"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070b;font-family:sans-serif;color:#f7f3ee}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.76),rgba(0,0,0,.10) 32%,rgba(0,0,0,.16) 58%,rgba(0,0,0,.82))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(255,255,255,.15) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:160px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#e6b07a}
.eyebrow:before{content:"";width:52px;height:4px;background:#e6b07a;border-radius:99px}
#cover h1{margin-top:28px;font-size:130px;line-height:1.03;font-weight:950;max-width:920px;text-wrap:balance}
#cover .sub{margin-top:28px;font-size:37px;line-height:1.46;color:#d8d0c5;font-weight:650;max-width:880px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(230,176,122,.55);color:#f3d7b0;background:rgba(10,10,14,.52);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:188px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(6,5,10,.82),rgba(6,5,10,.48));border-left:8px solid #e6b07a}
.fullLabel .rank{font-size:30px;font-weight:900;color:#e6b07a}
.fullLabel h2{margin-top:14px;font-size:72px;line-height:1.07;font-weight:950}
.fullLabel .tag{margin-top:18px;font-size:40px;line-height:1.28;font-weight:850;color:#f1cf9c}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.4;font-weight:650;color:#cfc6ba}
.fullLabel.topRank{border-left-color:#ff5c8a}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff79a3}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(6,5,10,.70);border:1px solid rgba(230,176,122,.58);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#e6b07a}
.miniLabel strong{font-size:36px;font-weight:900}
.miniLabel.topRank{border-color:rgba(255,92,138,.78)}
.miniLabel.topRank span{color:#ff79a3}
#outro{position:absolute;z-index:5;inset:0;padding:144px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#e6b07a}
#outro h2{margin-top:18px;font-size:62px;line-height:1.16;font-weight:950;max-width:920px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(6,5,10,.62);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#e6b07a}
#outro li:first-child span{color:#ff79a3}
#outro li strong{font-size:33px;font-weight:900;text-align:right}
#outro .close{margin-top:30px;font-size:29px;line-height:1.5;color:#d8d0c5;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:96px;text-align:center}
#cta .v{font-size:46px;font-weight:950;color:#ff79a3;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#e6b07a;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>赵传最难的5首歌</h1>'
    '<p class="sub">铁汉柔情的另一面——粗粝的高音、撕裂的爆发、长句的气息，每一首都是嗓子的极限考验。</p></div>'
    '<div class="chips"><span>撕裂高音</span><span>粗粝爆发</span><span>长气口</span><span>摇滚嗓</span><span>情绪支撑</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>赵传的难，是把粗粝和温柔，同时塞进一把嗓子里。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：我很丑可是我很温柔、红高粱、爱要怎么说出口、给所有知道我名字的人、我是一只小小鸟。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">你最想为哪一首？评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.from("#cover h1",{{scale:1.045,duration:.9,ease:"power3.out",transformOrigin:"left top"}},0);
tl.from("#cover .eyebrow",{{x:-20,duration:.6,ease:"power2.out"}},0);
tl.from("#cover .sub",{{y:18,duration:.55,ease:"power2.out"}},0.15);
tl.from("#cover .chips span",{{y:16,duration:.5,ease:"power2.out",stagger:.07}},0.2);
tl.to("#cover h1",{{scale:1.02,duration:3.4,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"left top"}},1.4);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
tl.from("#cta .v",{{y:26,opacity:0,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.from("#cta .f",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(cta_voice+0.35)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "zhaochuan-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
