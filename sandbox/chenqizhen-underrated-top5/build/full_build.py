#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 陈绮贞最被低估的5首歌."""
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
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
INTRO_CLIP = "vert_juli"
OUTRO_CLIP = "vert_fuxiu"

# Per-song gain compensation after QA. Keep at 1.0 until volumedetect proves otherwise.
MGAIN = {}


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

items = [
    {
        "key": "p5_juli", "clip": "vert_juli", "no": "05",
        "name": "《距离》", "plain": "距离", "show": 30.0,
        "tag": "一封永远寄不出去的信",
        "note": "《Groupies 吉他手》时期的隐藏宝藏",
    },
    {
        "key": "p4_taicongming", "clip": "vert_taicongming", "no": "04",
        "name": "《太聪明》", "plain": "太聪明", "show": 31.0,
        "tag": "爱情里的自我觉察写得太早",
        "note": "二十岁听好听，三十岁听会突然刺回来",
    },
    {
        "key": "p3_yigui", "clip": "vert_yigui", "no": "03",
        "name": "《躺在你的衣柜》", "plain": "躺在你的衣柜", "show": 31.0,
        "tag": "怪、可爱、又有点悲伤",
        "note": "真爱粉神曲，少女感后来越来越少见",
    },
    {
        "key": "p2_wanmei80", "clip": "vert_wanmei80", "no": "02",
        "name": "《80%完美的日子》", "plain": "80%完美的日子", "show": 25.0,
        "tag": "不再纠结爱情，开始观察生活",
        "note": "听十年会越来越喜欢的后期遗珠",
    },
    {
        "key": "p1_fuxiu", "clip": "vert_fuxiu", "no": "01",
        "name": "《腐朽》", "plain": "腐朽", "show": 34.0,
        "tag": "冷静到残忍的时间感",
        "note": "《华丽的冒险》里最陈绮贞的歌之一",
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
    end = q(full_start + item["show"])
    block = {
        **item,
        "start": q(t),
        "end": end,
        "narr_start": narr_start,
        "narr_end": narr_end,
        "full_start": full_start,
    }
    blocks.append(block)
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
planned_total = q(cta_voice_end + OUTRO_TAIL)


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

for block in blocks:
    seg_dur = q(block["end"] - block["start"])
    narr_end_local = q(LEAD + block["voice_dur"])
    full_start_local = q(block["full_start"] - block["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(block["key"], 1.0)
    out = f"seg_{block['key']}.wav"
    run(
        [
            "ffmpeg", "-v", "error",
            "-i", f"{C}/{block['clip']}.mp4",
            "-i", f"{A}/{block['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(planned_total - outro_start)
cta_local = q(cta_voice - outro_start)
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
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, INTRO_CLIP)]
for idx, block in enumerate(blocks, start=1):
    videos.append(video_tag(idx, block["start"], q(block["end"] - block["start"]), block["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), OUTRO_CLIP))

labels = []
tweens = []
for idx, block in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(block["full_start"] - block["start"])
    mdur = q(block["end"] - block["full_start"])
    rank_class = " topRank" if block["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{block["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {block["no"]} 名</div><h2>{block["name"]}</h2><p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{block["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{block["no"]}</span><strong>{block["plain"]}</strong></section>'
    )
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(block["start"]+.18)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:44,opacity:0}},{{y:0,opacity:1,duration:.62,ease:"power3.out"}},{q(block["start"]+.35)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(block["start"]+.72)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power1.out"}},{q(block["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(block["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(block["full_start"])});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-26,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out"}},{q(block["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("01", "腐朽"),
        ("02", "80%完美的日子"),
        ("03", "躺在你的衣柜"),
        ("04", "太聪明"),
        ("05", "距离"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#090b0b;font-family:sans-serif;color:#f4f0e8}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#090b0b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,10,10,.80),rgba(8,10,10,.16) 31%,rgba(8,10,10,.20) 58%,rgba(8,10,10,.86))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.12;background:repeating-linear-gradient(0deg,rgba(244,240,232,.12) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:148px 76px 134px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(8,10,10,.70),rgba(8,10,10,.16) 34%,rgba(8,10,10,.20) 60%,rgba(8,10,10,.84))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:800;color:#9fc5aa;letter-spacing:.08em}
.eyebrow:before{content:"";width:54px;height:4px;background:#9fc5aa;border-radius:99px}
#cover h1{margin-top:28px;font-family:serif;font-size:118px;line-height:1.08;font-weight:900;max-width:940px;text-shadow:0 6px 42px rgba(0,0,0,.62)}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.5;color:#d9d1c3;font-weight:500;max-width:886px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:920px}
.chips span{border:1px solid rgba(159,197,170,.52);color:#dcebdd;background:rgba(8,10,10,.52);font-size:28px;font-weight:700;padding:12px 19px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:196px;padding:35px 36px 39px;background:linear-gradient(135deg,rgba(8,10,10,.86),rgba(8,10,10,.46));border-left:8px solid #9fc5aa;border-radius:4px;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:31px;font-weight:900;color:#9fc5aa;letter-spacing:.12em}
.fullLabel h2{font-family:serif;margin-top:14px;font-size:88px;line-height:1.06;font-weight:900}
.fullLabel .tag{margin-top:19px;font-size:42px;line-height:1.28;font-weight:800;color:#d8eadc}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.42;font-weight:500;color:#c8c1b5}
.fullLabel.topRank{border-left-color:#d9b56f;background:linear-gradient(135deg,rgba(10,9,7,.88),rgba(10,9,7,.48))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#d9b56f}
.miniLabel{position:absolute;z-index:5;top:94px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(8,10,10,.66);border:1px solid rgba(159,197,170,.56);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:900;color:#9fc5aa}
.miniLabel strong{font-family:serif;font-size:39px;font-weight:900}
.miniLabel.topRank{border-color:rgba(217,181,111,.74)}
.miniLabel.topRank span{color:#d9b56f}
#outro{position:absolute;z-index:5;inset:0;padding:140px 76px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(8,10,10,.28),rgba(8,10,10,.78))}
#outro .small{font-size:32px;font-weight:900;color:#9fc5aa;letter-spacing:.12em}
#outro h2{font-family:serif;margin-top:20px;font-size:68px;line-height:1.18;font-weight:900;max-width:925px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:22px;padding:18px 24px;background:rgba(8,10,10,.58);border:1px solid rgba(244,240,232,.12);border-radius:9px}
#outro li span{font-size:35px;font-weight:900;color:#9fc5aa}
#outro li:first-child{background:rgba(217,181,111,.12);border-color:rgba(217,181,111,.36)}
#outro li:first-child span{color:#d9b56f}
#outro li strong{font-family:serif;font-size:39px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:32px;line-height:1.52;color:#d9d1c3;font-weight:500}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:102px;text-align:center;padding:22px 20px;background:rgba(8,10,10,.62);border:1px solid rgba(217,181,111,.38);border-radius:10px}
#cta .v{font-size:45px;font-weight:900;color:#d9b56f;line-height:1.22}
#cta .f{margin-top:16px;font-size:35px;font-weight:800;color:#9fc5aa;letter-spacing:.12em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 创作女声</div><h1>陈绮贞最被低估的5首歌</h1>'
    '<p class="sub">在那些被反复提起的代表作之外，她还有几首歌，安静、锋利、越长大越听得懂。</p></div>'
    '<div class="chips"><span>时间</span><span>距离</span><span>少女感</span><span>生活观察</span><span>真爱粉向</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>陈绮贞最动人的，常常不是把情绪说满，而是轻轻放在那里，等你很多年后自己听懂。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：距离、太聪明、躺在你的衣柜、80%完美的日子、腐朽。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.018,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.3);
tl.to("#cover",{{opacity:0,duration:.4,ease:"power1.in"}},{q(intro_end-.55)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.18)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(outro_start+2.18)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power1.out"}},{q(cta_voice+0.35)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "chenqizhen-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
