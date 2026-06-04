#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ns = runpy.run_path(str(ROOT / "build" / "full_build.py"))

CSS = ns["CSS"]
C = ns["C"]
INTRO_D = ns["INTRO_D"]
OUTRO_D = ns["OUTRO_D"]
blocks = ns["blocks"]
flash_items = ns["flash_items"]

SEGDIR = ROOT / "segments"
SEGDIR.mkdir(exist_ok=True)


def num(value):
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def video(id_, src, start, duration, track, cls="main-video", media_start=None):
    ms = f' data-media-start="{num(media_start)}"' if media_start is not None else ""
    return (
        f'<video id="{id_}" class="clip {cls}" data-start="{num(start)}" '
        f'data-duration="{num(duration)}" data-track-index="{track}" '
        f'src="{C}/{src}.mp4" muted playsinline{ms}></video>'
    )


def common_layers(duration):
    d = num(duration)
    return f"""
<div id="global-vignette" class="clip" data-start="0" data-duration="{d}" data-track-index="10"></div>
<div id="grain" class="clip" data-start="0" data-duration="{d}" data-track-index="11"></div>
<div id="stage-frame" class="clip stage-frame" data-start="0" data-duration="{d}" data-track-index="12"></div>
"""


def page(comp_id, duration, body):
    return f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1080,height=1920">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-duration="{num(duration)}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["{comp_id}"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>"""


segments = []

intro_bits = []
for i, (src, media_start, label) in enumerate(flash_items):
    start = round(i * 0.72, 3)
    intro_bits.append(video(f"flash{i}", src, start, 0.86, 20 + i, "flash-video", media_start))
    intro_bits.append(
        f'<div id="fc{i}" class="clip flash-caption" data-start="{num(start)}" '
        f'data-duration=".72" data-track-index="{70 + i}">{label}</div>'
    )
intro_bits.append(video("intro_bg", "top2_singer2024", 2.7, round(INTRO_D - 2.7, 3), 0, "main-video", 0))
intro_bits.append(common_layers(INTRO_D))
intro_bits.append(f"""
<section id="intro-title" class="clip" data-start="3.05" data-duration="{num(INTRO_D - 3.05)}" data-track-index="25">
  <div class="eyebrow">只看现场</div>
  <h1>《拯救》Live<br><b>完成度TOP5</b></h1>
  <div class="rule">不看情怀滤镜，不做绝对权威</div>
  <div class="criteria"><span>音准</span><span>气息</span><span>高音质量</span><span>现场压力</span><span>情绪推进</span></div>
</section>
""")
segments.append(("part00_intro", INTRO_D, "".join(intro_bits)))

for i, b in enumerate(blocks):
    duration = b["L"]
    full_start = round(b["full"] - b["start"], 3)
    full_duration = round(b["end"] - b["full"], 3)
    card_d = max(round(full_start - 0.25, 3), 1)
    rank_one = "rank-one" if b["no"] == "TOP1" else ""
    tags = "".join(f"<span>{x}</span>" for x in b["tags"])
    bits = [
        video(f"vid_{b['no'].lower()}", b["clip"], 0, duration, i, "main-video"),
        common_layers(duration),
        f"""
<section id="card{i}" class="clip rank-card {rank_one}" data-start="0.1" data-duration="{num(card_d)}" data-track-index="{40+i}">
  <div class="rank-no">{b["no"]}</div>
  <div class="rank-title">{b["title"]}</div>
  <div class="rank-sub">{b["subtitle"]}</div>
  <div class="rank-tags">{tags}</div>
</section>
<section id="show{i}" class="clip show-label {rank_one}" data-start="{num(full_start)}" data-duration="{num(full_duration)}" data-track-index="{50+i}">
  <div><b>{b["no"]}</b><span>{b["title"]}</span></div>
  <p>{b["transition"]}</p>
</section>
""",
    ]
    segments.append((f"part{i+1:02d}_{b['no'].lower()}", duration, "".join(bits)))

outro_bits = [
    video("outro_bg", "top1_korea5", 0, OUTRO_D, 7, "main-video", 8),
    common_layers(OUTRO_D),
    f"""
<section id="outro" class="clip" data-start="0.2" data-duration="{num(OUTRO_D - 0.2)}" data-track-index="66">
  <h2>你心中的《拯救》最强Live是哪一版？</h2>
  <p>《歌手2024》能反超中韩歌会吗？</p>
  <p class="fine">本期排名按演唱完成度、现场状态与社区讨论综合判断，欢迎补充其他版本。</p>
</section>
""",
]
segments.append(("part06_outro", OUTRO_D, "".join(outro_bits)))

manifest = []
for comp_id, duration, body in segments:
    rel = f"segments/{comp_id}.html"
    (ROOT / rel).write_text(page(comp_id, duration, body), encoding="utf-8")
    manifest.append({"id": comp_id, "file": rel, "duration": round(float(duration), 3)})

(ROOT / "segments" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
