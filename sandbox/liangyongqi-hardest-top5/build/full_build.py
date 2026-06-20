#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Gigi Leung (梁咏琪) hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 34.0
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {"p2_huahuo": 1.10, "p4_xianqi": 1.34}   # QA: huahuo -13.3 (ease), xianqi -16.4 (lift +2.5dB) → cluster ~-14dB
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0            # outro 升华 → 固定 CTA 的消化位（见 CONVENTIONS「固定结尾配音」）


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

items = [
    {
        "key": "p5_gaomei",
        "clip": "vert_gaomei",
        "no": "05",
        "name": "《高妹正传》",
        "plain": "高妹正传",
        "tag": "看起来轻巧，最难举重若轻",
        "note": "节奏、咬字、灵动感，一用力就笨",
    },
    {
        "key": "p4_xianqi",
        "clip": "vert_xianqi",
        "no": "04",
        "name": "《嫌弃》",
        "plain": "嫌弃",
        "tag": "越拧越难，藏着锋利",
        "note": "粤语咬字要清，情绪不能喊成苦情",
    },
    {
        "key": "p3_yanwu",
        "clip": "vert_yanwu",
        "no": "03",
        "name": "《烟雾弥漫》",
        "plain": "烟雾弥漫",
        "tag": "虚实之间，最吃气息",
        "note": "前段要虚，副歌要撑，音准不能晃",
    },
    {
        "key": "p2_huahuo",
        "clip": "vert_huahuo",
        "no": "02",
        "name": "《花火》",
        "plain": "花火",
        "tag": "明亮、脆弱，又要飞起来",
        "note": "清亮声线，飞得起还不能唱薄",
    },
    {
        "key": "p1_yuanlai",
        "clip": "vert_yuanlai",
        "no": "01",
        "name": "《原来爱情这么伤》",
        "plain": "原来爱情这么伤",
        "tag": "副歌一路走高，唱到崩塌",
        "note": "声音要干净稳，情绪到了不能先阵亡",
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
        "-i", f"{C}/vert_gaomei.mp4",
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
        "-i", f"{C}/vert_yuanlai.mp4",
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


videos = [video_tag(0, 0, intro_end, "vert_gaomei")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_yuanlai"))

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
    for n, name in [("01", "原来爱情这么伤"), ("02", "花火"), ("03", "烟雾弥漫"), ("04", "嫌弃"), ("05", "高妹正传")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080c;font-family:sans-serif;color:#f6f4ef}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07080c}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.74),rgba(0,0,0,.08) 30%,rgba(0,0,0,.14) 56%,rgba(0,0,0,.82))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.11;background:repeating-linear-gradient(0deg,rgba(255,255,255,.15) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:158px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#e6b07a}
.eyebrow:before{content:"";width:52px;height:4px;background:#e6b07a;border-radius:99px}
#cover h1{margin-top:30px;font-size:132px;line-height:1.02;font-weight:950;max-width:920px;text-wrap:balance;text-shadow:0 4px 38px rgba(0,0,0,.6)}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.46;color:#ddd6ca;font-weight:650;max-width:880px;text-shadow:0 2px 16px rgba(0,0,0,.7)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(230,176,122,.55);color:#f3d7b0;background:rgba(8,9,13,.52);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:182px;padding:34px 34px 38px;background:linear-gradient(135deg,rgba(6,6,11,.84),rgba(6,6,11,.46));border-left:8px solid #e6b07a;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:31px;font-weight:900;color:#e6b07a;letter-spacing:.04em}
.fullLabel h2{margin-top:14px;font-size:82px;line-height:1.06;font-weight:950}
.fullLabel .tag{margin-top:18px;font-size:42px;line-height:1.26;font-weight:850;color:#f1cf9c}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.4;font-weight:650;color:#cfc6ba}
.fullLabel.topRank{border-left-color:#ff5c8a}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ff79a3}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(6,6,11,.70);border:1px solid rgba(230,176,122,.58);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#e6b07a}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(255,92,138,.78)}
.miniLabel.topRank span{color:#ff79a3}
#outro{position:absolute;z-index:5;inset:0;padding:140px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#e6b07a;letter-spacing:.06em}
#outro h2{margin-top:18px;font-size:66px;line-height:1.16;font-weight:950;max-width:920px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(6,6,11,.62);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#e6b07a}
#outro li:first-child span{color:#ff79a3}
#outro li strong{font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:32px;font-size:31px;line-height:1.46;color:#ddd6ca;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:150px;text-align:center}
#cta .v{font-size:48px;font-weight:950;color:#ff79a3;line-height:1.2}
#cta .f{margin-top:16px;font-size:37px;font-weight:850;color:#e6b07a;letter-spacing:.12em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>梁咏琪最难的5首歌</h1>'
    '<p class="sub">高妹的另一面——清亮声线背后，是粤语咬字、气息控制，和唱稳了才显功力的分寸。</p></div>'
    '<div class="chips"><span>粤语咬字</span><span>气息控制</span><span>清亮声线</span><span>情绪分寸</span><span>现场稳定</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>梁咏琪的难，是把功夫，都藏进听起来很轻松的旋律里。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期按难度从第五到第一收束：高妹正传、嫌弃、烟雾弥漫、花火、原来爱情这么伤。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">你最想为哪一首投票？</div><div class="f">点赞 · 收藏 · 关注</div></section>'
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "liangyongqi-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
