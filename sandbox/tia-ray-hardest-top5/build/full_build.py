#!/usr/bin/env python3
"""Build vertical clips, master.wav and HyperFrames HTML for 袁娅维最难5首歌."""

import contextlib
import json
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import song_cfg as cfg

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

LEAD = cfg.LEAD
DIG = cfg.DIG
BED = cfg.BED
VOICE_GAIN = cfg.VOICE_GAIN
INTRO_VOICE_START = cfg.INTRO_VOICE_START
INTRO_GAP = cfg.INTRO_GAP
OUTRO_TAIL = cfg.OUTRO_TAIL
DIGEST_O = cfg.DIGEST_O
TAIL_BUF = cfg.TAIL_BUF


def dur(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "r")) as handle:
        return round(handle.getnframes() / handle.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value) -> float:
    return round(float(value), 3)


def clip_name(item):
    return "vert_" + item["key"].split("_", 1)[1]


def make_vert(
    src: Path,
    out: Path,
    start: float,
    length: float,
    crop: str,
    delogo: str | None = None,
    delogo_enable: str | None = None,
):
    """Create a 1080x1920 vertical clip with dense keyframes and source audio."""
    cleanup = ""
    if delogo:
        x, y, w, h = delogo.split(":")
        enable = ""
        if delogo_enable:
            expr = delogo_enable.replace(",", r"\,")
            enable = f":enable='{expr}'"
        cleanup = f",delogo=x={x}:y={y}:w={w}:h={h}{enable}"
    vf = (
        f"crop={crop}{cleanup},split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,gblur=sigma=30,eq=brightness=-0.34:saturation=1.04[bgb];"
        "[fg]scale=1080:-2[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run(
        [
            "ffmpeg", "-v", "error",
            "-ss", str(q(start)), "-t", str(q(length)),
            "-i", str(src),
            "-filter_complex", vf,
            "-map", "[v]", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(out), "-y",
        ]
    )


def song_envelope(narr_end_local: float, full_start_local: float, show_end_local: float, seg_dur: float):
    swell = q(narr_end_local + 0.25)
    fade_start = q(show_end_local)
    fade_len = max(0.35, q(seg_dur - fade_start))
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(between(t,{full_start_local},{fade_start}))*1.0"
        f"+(gte(t,{fade_start}))*max(0,1.0-(t-{fade_start})/{fade_len})"
    )


items = []
for src in cfg.SONGS:
    item = {**src, "clip": clip_name(src), "voice_dur": dur(A / f"{src['key']}.wav")}
    pre = q(LEAD + item["voice_dur"] + 0.25 + DIG)
    item["clip_start"] = q(max(0, item["vocal_start"] - pre))
    item["clip_duration"] = q(pre + item["show"] + TAIL_BUF)
    item["full_start_local"] = q(item["vocal_start"] - item["clip_start"])
    items.append(item)

C.mkdir(parents=True, exist_ok=True)
for item in items:
    make_vert(
        ROOT / item["source"],
        C / f"{item['clip']}.mp4",
        item["clip_start"],
        item["clip_duration"],
        item["crop"],
        item.get("delogo"),
        item.get("delogo_enable"),
    )
    print(f"{item['key']} clip_start={item['clip_start']} full_local={item['full_start_local']} show={item['show']}")

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + item["show"] + 0.45)
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start})
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
planned_total = q(cta_voice_end + OUTRO_TAIL)

segments = []

intro_dur = intro_end
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{cfg.INTRO_CLIP}.mp4",
        "-i", f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={q(intro_dur-0.9)}:d=0.9[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ]
)
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    show_end_local = q(full_start_local + b["show"])
    env = song_envelope(narr_end_local, full_start_local, show_end_local, seg_dur)
    out = f"seg_{b['key']}.wav"
    music_gain = cfg.MGAIN.get(b["key"], 1.0)
    run(
        [
            "ffmpeg", "-v", "error",
            "-i", f"{C}/{b['clip']}.mp4",
            "-i", f"{A}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=level=disabled:limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(planned_total - outro_start)
cta_local = q(cta_voice - outro_start)
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{cfg.OUTRO_CLIP}.mp4",
        "-i", f"{A}/outro.wav",
        "-i", f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.6)}:d=1.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ]
)
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)

timeline = {"total": total, "intro_end": intro_end, "outro_start": outro_start, "cta_voice": cta_voice, "blocks": blocks}
(ROOT / "build" / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "tia-ray-hardest-top5"}, ensure_ascii=False), encoding="utf-8")


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, cfg.INTRO_CLIP)]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), cfg.OUTRO_CLIP))

labels = []
tweens = []
for idx, b in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    top_class = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{top_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="4">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{top_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="5">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,autoAlpha:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,autoAlpha:0,duration:.62,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,autoAlpha:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,autoAlpha:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.96)});')
    tweens.append(f'tl.to("#{fid}",{{autoAlpha:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{autoAlpha:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,autoAlpha:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{s["no"]}</span><strong>{s["plain"]}</strong></li>' for s in reversed(cfg.SONGS)
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07070B;font-family:"Noto Sans SC","PingFang SC",sans-serif;color:#F7F1E8;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07070B}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(180deg,rgba(7,7,11,.82),rgba(7,7,11,.20) 32%,rgba(7,7,11,.28) 58%,rgba(7,7,11,.88))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.11;background:repeating-linear-gradient(0deg,rgba(255,255,255,.15) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:150px 74px 145px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#D8A24C;letter-spacing:.12em}
.eyebrow:before{content:"";width:54px;height:4px;background:#D8A24C;border-radius:99px}
#cover h1{margin-top:28px;font-family:"Noto Serif SC","Songti SC",serif;font-size:126px;line-height:1.03;font-weight:900;max-width:930px;text-shadow:0 18px 58px rgba(0,0,0,.70)}
#cover .sub{margin-top:28px;font-size:39px;line-height:1.45;color:#D8CED8;font-weight:650;max-width:900px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:910px}
.chips span{border:1px solid rgba(216,162,76,.58);color:#F5D49C;background:rgba(7,7,11,.56);font-size:28px;font-weight:780;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:68px;right:68px;bottom:178px;padding:35px 35px 39px;background:linear-gradient(135deg,rgba(7,7,11,.88),rgba(33,20,46,.56));border-left:8px solid #D8A24C;box-shadow:0 28px 88px rgba(0,0,0,.42)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:900;color:#D8A24C}
.fullLabel h2{margin-top:14px;font-family:"Noto Serif SC","Songti SC",serif;font-size:78px;line-height:1.08;font-weight:900}
.fullLabel .tag{margin-top:18px;font-size:40px;line-height:1.28;font-weight:850;color:#F2CE91}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.42;font-weight:650;color:#D4C8D2}
.fullLabel.topRank{border-left-color:#C43A54}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#FF758C}
.miniLabel{position:absolute;z-index:5;top:94px;left:56px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(7,7,11,.72);border:1px solid rgba(216,162,76,.60);border-radius:8px;box-shadow:0 18px 52px rgba(0,0,0,.32)}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:950;color:#D8A24C}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(196,58,84,.86)}
.miniLabel.topRank span{color:#FF758C}
#outro{position:absolute;z-index:5;inset:0;padding:138px 74px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#D8A24C;letter-spacing:.12em}
#outro h2{margin-top:20px;font-family:"Noto Serif SC","Songti SC",serif;font-size:63px;line-height:1.18;font-weight:900;max-width:930px}
#outro ol{margin-top:38px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(7,7,11,.66);border:1px solid rgba(255,255,255,.12);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:34px;font-weight:950;color:#D8A24C}
#outro li:first-child span{color:#FF758C}
#outro li strong{font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:30px;font-size:32px;line-height:1.48;color:#D4C8D2;font-weight:650}
#cta{position:absolute;z-index:6;left:74px;right:74px;bottom:92px;text-align:center}
#cta .v{font-size:46px;font-weight:950;color:#FF758C;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#D8A24C;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{intro_end}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>袁娅维最难的5首歌</h1>'
    '<p class="sub">不只是高音。真正难的是律动、转音、咬字、声压和情绪同时在线。</p></div>'
    '<div class="chips"><span>R&B / Soul</span><span>高位爆发</span><span>华丽转音</span><span>律动控制</span><span>情绪层次</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>袁娅维的难，不是单点炫技，是把技术、律动和情绪同时唱成自由。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从《阿楚姑娘》的克制，到《Starfall》的大动态，这五首刚好把她最难复制的能力串起来。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="8">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.from("#cover .chips span",{{y:12,autoAlpha:0,duration:.42,ease:"power2.out",stagger:.08}},1.0);
tl.to("#cover",{{autoAlpha:0,duration:.38,ease:"power1.in"}},{q(intro_end-.42)});
tl.set("#cover",{{autoAlpha:0}},{intro_end});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,autoAlpha:0,duration:.45,ease:"power2.out"}},{q(outro_start+.25)});
tl.from("#outro h2",{{y:40,autoAlpha:0,duration:.65,ease:"power3.out"}},{q(outro_start+.48)});
tl.from("#outro li",{{y:24,autoAlpha:0,duration:.45,ease:"power2.out",stagger:.07}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:20,autoAlpha:0,duration:.45,ease:"power2.out"}},{q(outro_start+1.75)});
tl.to("#outro",{{autoAlpha:0,duration:.38,ease:"power1.in"}},{q(cta_voice-.42)});
tl.set("#outro",{{autoAlpha:0}},{q(cta_voice-.05)});
tl.from("#cta .v",{{y:28,autoAlpha:0,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.from("#cta .f",{{y:20,autoAlpha:0,duration:.5,ease:"power2.out"}},{q(cta_voice+.35)});
"""

html = f"""<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="vendor/gsap.min.js"></script>
<style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>
"""
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("wrote index.html")
