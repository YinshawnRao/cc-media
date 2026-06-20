#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 光良最被低估5首 (倒数 5->1).

- 女声旁白 audio/*.wav；每首自包含音频段 bed->swell->showcase，loudnorm=I=-14。
- 音乐源 = music/<key>.wav（同源曲=clip 同窗音轨；解耦曲=录音室副歌），footage = clips/vert_<key>.mp4。
- intro/outro 音床从 COVER_SRC 抽（soft / chorus），避免片头片尾 dead-air。
- cover 不剧透排名；outro 揭晓 5->1 榜单；固定 CTA 为全片最后一句（作品 outro 不带投票问句）。
"""
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
M = ROOT / "music"

LEAD, DIG, BED = cfg.LEAD, cfg.DIG, cfg.BED
VOICE_GAIN, MGAIN = cfg.VOICE_GAIN, cfg.MGAIN
INTRO_VOICE_START, INTRO_GAP, BETWEEN = cfg.INTRO_VOICE_START, cfg.INTRO_GAP, cfg.BETWEEN
OUTRO_TAIL, DIGEST_O = cfg.OUTRO_TAIL, cfg.DIGEST_O
OUTRO_BED_START = 200.0   # ruguo 副歌段作 outro 床（不用歌曲淡出尾）


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(v):
    return round(float(v), 3)


items = [{"key": s["key"], "clip": "vert_" + s["key"], "no": s["no"], "name": s["name"],
          "plain": s["plain"], "tag": s["tag"], "note": s["note"], "show": s["show"]} for s in cfg.SONGS]

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
    blocks.append({**item, "start": q(t), "end": end, "narr_start": narr_start,
                   "narr_end": narr_end, "full_start": full_start})
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)

# --- intro/outro music beds from COVER_SRC ---
intro_dur = intro_end
outro_dur = q(total - outro_start)
run(["ffmpeg", "-v", "error", "-ss", str(cfg.COVER_START), "-i", str(ROOT / cfg.COVER_SRC),
     "-t", str(intro_dur), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(M / "intro_bed.wav"), "-y"])
run(["ffmpeg", "-v", "error", "-ss", str(OUTRO_BED_START), "-i", str(ROOT / cfg.COVER_SRC),
     "-t", str(outro_dur), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(M / "outro_bed.wav"), "-y"])


def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

run([
    "ffmpeg", "-v", "error", "-i", str(M / "intro_bed.wav"), "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    run([
        "ffmpeg", "-v", "error", "-i", str(M / f"{b['key']}.wav"), "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

cta_local = q(cta_voice - outro_start)
run([
    "ffmpeg", "-v", "error", "-i", str(M / "outro_bed.wav"), "-i", f"{A}/outro.wav", "-i", f"{A}/outro_cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.16,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{n}'\n" for n in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
planned_total = total
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
            f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>')


videos = [video_tag(0, 0, intro_end, cfg.INTRO_CLIP)]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), b["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), cfg.OUTRO_CLIP))

labels, tweens = [], []
for idx, b in enumerate(blocks):
    fid, mid = f"full{idx}", f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    rank_class = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2><p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>')
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>')
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.72)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [("01", "如果你还爱我"), ("02", "握你的手"), ("03", "期限"), ("04", "海边"), ("05", "住在遥远的星球")])

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0b12;font-family:"Noto Sans SC",sans-serif;color:#f3f0ea}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a0b12}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,9,16,.82),rgba(8,9,16,.12) 32%,rgba(8,9,16,.18) 56%,rgba(8,9,16,.84))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.08;background:repeating-linear-gradient(0deg,rgba(220,225,255,.14) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:150px 76px 144px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;color:#d8b06a;letter-spacing:.05em}
.eyebrow:before{content:"";width:54px;height:4px;background:#d8b06a;border-radius:99px}
#cover h1{font-family:"Noto Serif SC",serif;font-size:128px;line-height:1.05;font-weight:900;max-width:920px;text-wrap:balance;text-shadow:0 6px 40px rgba(0,0,0,.6)}
#cover .sub{margin-top:30px;font-size:38px;line-height:1.5;color:#d6d0dd;font-weight:500;max-width:880px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(216,176,106,.5);color:#ecd6a8;background:rgba(10,11,18,.46);font-size:29px;font-weight:600;padding:12px 20px;border-radius:9px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:196px;padding:36px 36px 40px;background:linear-gradient(135deg,rgba(10,11,18,.84),rgba(10,11,18,.42));border-left:8px solid #d8b06a;border-radius:4px;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:31px;font-weight:800;color:#d8b06a;letter-spacing:.14em}
.fullLabel h2{font-family:"Noto Serif SC",serif;margin-top:14px;font-size:88px;line-height:1.05;font-weight:900}
.fullLabel .tag{margin-top:20px;font-size:43px;line-height:1.28;font-weight:700;color:#ecd0a0}
.fullLabel .note{margin-top:12px;font-size:32px;line-height:1.4;font-weight:400;color:#cdc6d4}
.fullLabel.topRank{border-left-color:#ffcf7a}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ffd98c}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 22px;background:rgba(10,11,18,.62);border:1px solid rgba(216,176,106,.55);border-radius:9px}
.miniLabel span{font-size:44px;font-weight:900;color:#d8b06a}
.miniLabel strong{font-family:"Noto Serif SC",serif;font-size:40px;font-weight:800}
.miniLabel.topRank{border-color:rgba(255,207,122,.75)}
.miniLabel.topRank span{color:#ffd98c}
#outro{position:absolute;z-index:5;inset:0;padding:130px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:33px;font-weight:800;color:#d8b06a;letter-spacing:.14em}
#outro h2{font-family:"Noto Serif SC",serif;margin-top:20px;font-size:66px;line-height:1.18;font-weight:900;max-width:920px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:14px;width:100%}
#outro li{display:flex;align-items:center;gap:26px;padding:17px 24px;background:rgba(10,11,18,.58);border:1px solid rgba(230,230,255,.12);border-radius:10px}
#outro li span{font-size:35px;font-weight:900;color:#d8b06a;min-width:58px}
#outro li:first-child{background:rgba(255,207,122,.12);border-color:rgba(255,207,122,.34)}
#outro li:first-child span{color:#ffd98c}
#outro li strong{font-family:"Noto Serif SC",serif;font-size:42px;font-weight:800}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:120px;text-align:center}
#cta .v{font-size:46px;font-weight:900;color:#ffd98c;line-height:1.22}
#cta .f{margin-top:16px;font-size:36px;font-weight:800;color:#d8b06a;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0.2" data-duration="{q(intro_end-.35)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 唱作盘点</div><h1>光良最被低估的5首歌</h1>'
    '<p class="sub">在《童话》和《第一次》之外，这五首藏在专辑深处的歌，写着他最细腻、最不张扬的那点心事。</p></div>'
    '<div class="chips"><span>情歌王子</span><span>唱作实力</span><span>专辑遗珠</span><span>越听越有后劲</span><span>老歌迷私藏</span></div></section>')
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">完整榜单</div><h2>他最打动人的，是把最细腻的心事，写进最不张扬的歌里。</h2>'
    f'<ol>{ranking_rows}</ol></section>')
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>')
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow",{{opacity:1,x:0}},0);
tl.set("#cover h1",{{opacity:1,y:0}},0);
tl.set("#cover .sub",{{opacity:1,y:0}},0);
tl.set("#cover .chips span",{{opacity:1,y:0}},0);
tl.fromTo("#cover h1",{{scale:1}},{{scale:1.02,duration:3.4,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"0% 50%"}},1.0);
tl.to("#cover",{{opacity:0,duration:.4,ease:"power1.in"}},{q(intro_end-.55)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "guangliang-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
