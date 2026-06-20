#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for the Hacken Lee hardest top 5 video."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

SHOW = 38.0
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
MGAIN = {"p5_gaomei": 1.10}
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0


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
        "name": "《高妹》",
        "plain": "高妹",
        "tag": "轻快里最怕赶拍",
        "note": "节奏、咬字、换气和松弛度都要准",
    },
    {
        "key": "p4_feihua",
        "clip": "vert_feihua",
        "no": "04",
        "name": "《飞花》",
        "plain": "飞花",
        "tag": "高位旋律要柔，还要有支点",
        "note": "气息均匀、尾音干净，粤语轻重不能塌",
    },
    {
        "key": "p3_yueban",
        "clip": "vert_yueban",
        "no": "03",
        "name": "《月半小夜曲》",
        "plain": "月半小夜曲",
        "tag": "一开口就知道准不准",
        "note": "长线条、弱声、尾音、气息和音准全在考",
    },
    {
        "key": "p2_dahuitang",
        "clip": "vert_dahuitang",
        "no": "02",
        "name": "《大会堂演奏厅》",
        "plain": "大会堂演奏厅",
        "tag": "优雅外壳，咬字体能双杀",
        "note": "歌词密、叠字多、句子快，旋律还要端正",
    },
    {
        "key": "p1_buhui",
        "clip": "vert_buhui",
        "no": "01",
        "name": "《我不会唱歌》",
        "plain": "我不会唱歌",
        "tag": "跟钢琴赛跑，还不能跑飞",
        "note": "速度、切分、跳跃、高位句和字头都要稳",
    },
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
    end = q(full_start + SHOW)
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start})
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
cta_local = q(cta_voice - outro_start)
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/vert_buhui.mp4",
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
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_buhui"))

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
    tweens.append(f'tl.from("#{fid} .tag",{{x:-18,opacity:0,duration:.5,ease:"power4.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"sine.out"}},{q(b["start"]+.98)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "我不会唱歌"), ("02", "大会堂演奏厅"), ("03", "月半小夜曲"), ("04", "飞花"), ("05", "高妹")]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07070a;font-family:sans-serif;color:#f7efe2}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:radial-gradient(circle at 72% 18%,rgba(215,168,92,.24),rgba(215,168,92,0) 34%),linear-gradient(to bottom,rgba(0,0,0,.80),rgba(0,0,0,.13) 32%,rgba(42,8,18,.18) 58%,rgba(0,0,0,.86))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.13;background:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,rgba(255,255,255,0) 1px 4px);mix-blend-mode:overlay}
#score{position:absolute;inset:0;z-index:3;opacity:.20;background:repeating-linear-gradient(90deg,rgba(215,168,92,.22) 0 2px,rgba(215,168,92,0) 2px 118px)}
#cover{position:absolute;inset:0;z-index:5;padding:150px 72px 145px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#d7a85c;letter-spacing:.08em}
.eyebrow:before{content:"";width:52px;height:4px;background:#d7a85c;border-radius:99px}
#cover h1{margin-top:26px;font-family:serif;font-size:126px;line-height:1.05;font-weight:900;max-width:930px;text-wrap:balance}
#cover .sub{margin-top:28px;font-size:37px;line-height:1.46;color:#cfc2ad;font-weight:650;max-width:890px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:910px}
.chips span{border:1px solid rgba(215,168,92,.62);color:#f7efe2;background:rgba(7,7,10,.58);font-size:28px;font-weight:780;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:68px;right:68px;bottom:186px;padding:36px 34px 40px;background:linear-gradient(135deg,rgba(7,7,10,.86),rgba(42,8,18,.54));border-left:8px solid #d7a85c;box-shadow:0 24px 80px rgba(0,0,0,.38)}
.fullLabel .rank{font-size:30px;font-weight:900;color:#d7a85c}
.fullLabel h2{margin-top:14px;font-family:serif;font-size:78px;line-height:1.08;font-weight:900}
.fullLabel .tag{margin-top:18px;font-size:40px;line-height:1.28;font-weight:850;color:#f1cf9c}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:650;color:#cfc2ad}
.fullLabel.topRank{border-left-color:#f05a7d}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f05a7d}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(7,7,10,.72);border:1px solid rgba(215,168,92,.64);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#d7a85c;font-variant-numeric:tabular-nums}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(240,90,125,.82)}
.miniLabel.topRank span{color:#f05a7d}
#outro{position:absolute;z-index:5;inset:0;padding:144px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#d7a85c}
#outro h2{margin-top:18px;font-family:serif;font-size:68px;line-height:1.16;font-weight:900;max-width:910px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(7,7,10,.64);border:1px solid rgba(255,255,255,.13);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#d7a85c;font-variant-numeric:tabular-nums}
#outro li:first-child span{color:#f05a7d}
#outro li strong{font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:32px;font-size:31px;line-height:1.46;color:#cfc2ad;font-weight:650}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:96px;text-align:center}
#cta .v{font-size:46px;font-weight:950;color:#f05a7d;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#d7a85c;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="score" class="clip" data-start="0" data-duration="{total}" data-track-index="8"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>李克勤最难的5首歌</h1>'
    '<p class="sub">从轻快咬字到钢琴切分，从粤语长线条到现场稳定，真正的难，是把一切唱到像没有难度。</p></div>'
    '<div class="chips"><span>节奏切分</span><span>粤语咬字</span><span>气息线条</span><span>高位控制</span><span>现场稳定</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>李克勤的难，是把速度、咬字、气息和音准，都藏进稳定里。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这一期按难度从第五到第一收束：高妹、飞花、月半小夜曲、大会堂演奏厅、我不会唱歌。</p></section>'
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
tl.from("#cover .sub",{{y:18,duration:.55,ease:"sine.out"}},0.15);
tl.from("#cover .chips span",{{y:16,duration:.5,ease:"power4.out",stagger:.07}},0.2);
tl.to("#cover h1",{{scale:1.02,duration:3.4,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"left top"}},1.4);
tl.to("#cover",{{opacity:0,duration:.38,ease:"power1.in"}},{q(intro_end-.55)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power4.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"sine.out"}},{q(outro_start+2.0)});
tl.from("#cta .v",{{y:26,opacity:0,duration:.55,ease:"power3.out"}},{q(cta_voice)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "hackenlee-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
