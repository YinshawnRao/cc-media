#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 飞儿乐队最被低估的5首歌.

Structure:
cover -> intro -> 5x(reveal card during narration -> full-music showcase)
-> outro recap -> fixed CTA. The rendered HyperFrames video must be muxed with
the pre-mixed master.wav after render.
"""
import json
import shutil
import subprocess
from pathlib import Path

import song_config as cfg

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
ASRC = ROOT / "audio_src"
SEG = ROOT / "build" / "segs"
COVER = ROOT / "hf" / "cover_assets"
SEG.mkdir(parents=True, exist_ok=True)
COVER.mkdir(parents=True, exist_ok=True)

ACC = "#D6A95F"      # desert amber
ACC2 = "#72A7A5"     # weathered teal
GOLD = "#F2CD73"     # #1 gold


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def dur(p):
    return round(float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(p),
    ])), 3)


def f(x):
    return f"{round(float(x), 3)}"


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
for s in cfg.SONGS:
    s["voice"] = meta[s["key"]]["dur"]
d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")

# ---------------- timeline ----------------
intro_end = round(cfg.INTRO_VOICE_START + d_intro + cfg.INTRO_GAP, 3)
t = intro_end
for s in cfg.SONGS:
    vd = s["voice"]
    s["start"] = round(t, 3)
    s["narr_start"] = round(t + cfg.LEAD, 3)
    s["narr_end"] = round(s["narr_start"] + vd, 3)
    s["full_start"] = round(s["narr_end"] + 0.25 + cfg.DIG, 3)
    s["end"] = round(s["full_start"] + s["show"], 3)
    s["seg_dur"] = round(s["end"] - s["start"], 3)
    s["full_local"] = round(s["full_start"] - s["start"], 3)
    t = s["end"]
outro_start = round(t, 3)
outro_voice = round(outro_start + cfg.LEAD, 3)
outro_voice_end = round(outro_voice + d_outro, 3)
cta_voice = round(outro_voice_end + cfg.DIGEST_O, 3)
cta_voice_end = round(cta_voice + d_cta, 3)
TOTAL = round(cta_voice_end + cfg.OUTRO_TAIL, 3)
cta_local = round(cta_voice - outro_start, 3)
outro_dur = round(TOTAL - outro_start, 3)

print("intro_end", intro_end, "outro_start", outro_start, "TOTAL", TOTAL,
      f"= {int(TOTAL//60)}:{TOTAL%60:05.2f}")
for s in cfg.SONGS:
    print(f"  {s['no']} {s['plain']:6s} start={s['start']:7.2f} full={s['full_start']:7.2f} end={s['end']:7.2f}")


# =====================================================================
#  AUDIO
# =====================================================================
INTRO_BED = ASRC / "p1_yingxuzhidi.wav"
OUTRO_BED = ASRC / "p1_yingxuzhidi.wav"


def build_intro():
    d = intro_end
    va = cfg.INTRO_VOICE_START
    run(["ffmpeg", "-v", "error", "-i", INTRO_BED, "-i", A / "intro.wav", "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume={cfg.VOICE_GAIN}[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,"
         f"atrim=0:{d},asetpts=PTS-STARTPTS,volume=0.13,afade=t=in:st=0:d=1.0,afade=t=out:st={d-1.0}:d=1.0[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{d},alimiter=limit=0.95:level=disabled[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", SEG / "seg_intro.wav", "-y"])


def song_envelope(narr_end_local, full_local):
    swell = round(narr_end_local + 0.25, 3)
    return (
        f"(lt(t,0.8))*({cfg.BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{cfg.BED}"
        f"+(between(t,{swell},{full_local}))*({cfg.BED}+{1.0-cfg.BED}*(t-{swell})/{cfg.DIG})"
        f"+(gte(t,{full_local}))*1.0"
    )


def build_song(s):
    seg = s["seg_dur"]
    narr_end_local = round(cfg.LEAD + s["voice"], 3)
    env = song_envelope(narr_end_local, s["full_local"])
    music = ASRC / f"{s['key']}.wav"
    run(["ffmpeg", "-v", "error", "-i", music, "-i", A / f"{s['key']}.wav", "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cfg.LEAD*1000)}|{int(cfg.LEAD*1000)},volume={cfg.VOICE_GAIN}[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg},asetpts=PTS-STARTPTS,volume='{env}':eval=frame,volume={s['mgain']},"
         f"afade=t=out:st={seg-1.2}:d=1.2[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95:level=disabled[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", SEG / f"seg_{s['key']}.wav", "-y"])


def build_outro():
    d = outro_dur
    va = cfg.LEAD
    run(["ffmpeg", "-v", "error", "-i", OUTRO_BED, "-i", A / "outro.wav", "-i", A / "outro_cta.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume={cfg.VOICE_GAIN}[v1];"
         f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)},volume={cfg.VOICE_GAIN}[v2];"
         f"[v1][v2]amix=inputs=2:normalize=0:duration=longest[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,"
         f"atrim=0:{d},asetpts=PTS-STARTPTS,volume=0.18,afade=t=in:st=0:d=1.2,afade=t=out:st={d-1.6}:d=1.6[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{d},alimiter=limit=0.95:level=disabled[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", SEG / "seg_outro.wav", "-y"])


build_intro()
for s in cfg.SONGS:
    build_song(s)
build_outro()

names = ["seg_intro.wav"] + [f"seg_{s['key']}.wav" for s in cfg.SONGS] + ["seg_outro.wav"]
(SEG / "list.txt").write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", SEG / "list.txt",
     "-ac", "2", "-ar", "48000", ROOT / "master.wav", "-y"])
print("master:", dur(ROOT / "master.wav"), "planned:", TOTAL)

# Cover frame from the #1 showcase.
run(["ffmpeg", "-v", "error", "-ss", "7", "-i", ROOT / "clips" / "show_p1_yingxuzhidi.mp4",
     "-frames:v", "1", COVER / "cover.jpg", "-y"])


# =====================================================================
#  HTML
# =====================================================================
HF = ROOT / "hf"
HF.mkdir(exist_ok=True)
(HF / "clips_show").mkdir(exist_ok=True)
shutil.copy(ROOT / "master.wav", HF / "master.wav")
for s in cfg.SONGS:
    foot_dur = round(cfg.PREROLL + s["show"] + 0.5, 3)
    run(["ffmpeg", "-v", "error", "-i", ROOT / "clips" / f"show_{s['key']}.mp4", "-t", str(foot_dur),
         "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
         "-pix_fmt", "yuv420p", "-an", HF / "clips_show" / f"{s['key']}.mp4", "-y"])

CSS = r'''
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#070912;
  font-family:"Noto Sans SC",sans-serif;color:#F4EDDF;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#070912}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0}
#scrim{position:absolute;inset:0;z-index:3;
  background:linear-gradient(180deg,rgba(7,9,18,.78) 0%,rgba(7,9,18,.16) 24%,rgba(7,9,18,.24) 58%,rgba(7,9,18,.88) 100%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.07;mix-blend-mode:overlay;
  background:repeating-linear-gradient(0deg,rgba(255,255,255,.16) 0 1px,rgba(255,255,255,0) 1px 4px)}
.vig{position:absolute;inset:0;z-index:8;pointer-events:none;
  background:radial-gradient(ellipse at 50% 42%,rgba(0,0,0,0) 50%,rgba(0,0,0,.52) 100%)}

#cover{position:absolute;inset:0;z-index:40;overflow:hidden;background:#070912}
#cover .cv-bg{position:absolute;inset:0;background-size:cover;background-position:50% 38%;
  filter:brightness(.52) saturate(1.05) contrast(1.04);transform:scale(1.06)}
#cover .cv-shade{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(7,9,18,.58) 0%,rgba(7,9,18,.28) 34%,rgba(7,9,18,.66) 70%,rgba(7,9,18,.96) 100%)}
#cover .cv-wrap{position:absolute;left:78px;right:78px;bottom:142px}
.cv-eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:800;
  color:var(--acc);letter-spacing:.12em}
.cv-eyebrow:before{content:"";width:54px;height:4px;background:var(--acc);border-radius:99px}
.cv-h1{margin-top:30px;font-family:"Noto Serif SC",serif;font-weight:900;line-height:1.08;
  font-size:106px;letter-spacing:1px;text-shadow:0 6px 30px rgba(0,0,0,.62)}
.cv-h1 .em{color:var(--acc)}
.cv-sub{margin-top:30px;font-size:35px;line-height:1.55;color:#D9D0BF;font-weight:500;max-width:900px}
.cv-chips{margin-top:34px;display:flex;flex-wrap:wrap;gap:14px}
.cv-chips span{border:1px solid rgba(214,169,95,.46);color:#F0DEB8;background:rgba(10,11,18,.44);
  font-size:28px;font-weight:600;padding:11px 20px;border-radius:8px}

.reveal{position:absolute;inset:0;z-index:20;opacity:0;overflow:hidden;
  background:radial-gradient(ellipse at 50% 28%,#171920 0%,#0a0c13 60%,#06070d 100%)}
.rv-ghost{position:absolute;top:140px;left:0;right:0;text-align:center;
  font-family:"Noto Serif SC",serif;font-weight:900;font-size:560px;line-height:1;
  color:rgba(255,255,255,.052);letter-spacing:-10px}
.rv-wrap{position:absolute;left:88px;right:88px;top:748px}
.rv-rank{font-size:40px;font-weight:800;letter-spacing:.16em}
.rv-rule{width:90px;height:4px;border-radius:99px;margin:26px 0 30px}
.rv-title{font-family:"Noto Serif SC",serif;font-weight:900;font-size:126px;line-height:1.04;
  color:#FBF6EA;letter-spacing:1px}
.rv-meta{margin-top:30px;font-size:32px;font-weight:600;color:#C7BEAD;letter-spacing:.02em}
.rv-tag{margin-top:22px;font-size:42px;font-weight:800;letter-spacing:.01em}

.chip{position:absolute;left:64px;bottom:150px;z-index:15;display:flex;align-items:center;gap:20px;
  padding:16px 30px 16px 22px;border-radius:14px;opacity:0;
  background:linear-gradient(135deg,rgba(8,9,15,.84),rgba(8,9,15,.52));
  border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.chip .cno{font-family:"Noto Serif SC",serif;font-weight:900;font-size:58px;line-height:.9}
.chip .cnm{font-family:"Noto Serif SC",serif;font-weight:800;font-size:46px;color:#FBF6EA}
.chip .cbar{width:3px;align-self:stretch;border-radius:2px;background:rgba(255,255,255,.28)}

#outro{position:absolute;inset:0;z-index:30;opacity:0;overflow:hidden;padding:146px 80px;
  display:flex;flex-direction:column;justify-content:center;
  background:radial-gradient(ellipse at 50% 24%,#16191f 0%,#0a0c13 58%,#06070d 100%)}
#outro .ot-small{font-size:33px;font-weight:800;color:var(--acc);letter-spacing:.14em;opacity:0}
#outro .ot-h{margin-top:22px;font-family:"Noto Serif SC",serif;font-weight:900;font-size:61px;
  line-height:1.23;color:#FBF6EA;max-width:920px;opacity:0}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:14px}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 26px;
  background:rgba(10,11,18,.64);border:1px solid rgba(255,255,255,.10);border-radius:10px;opacity:0}
#outro li .li-l{display:flex;align-items:baseline;gap:20px}
#outro li .li-no{font-family:"Noto Serif SC",serif;font-size:38px;font-weight:900;color:var(--acc)}
#outro li .li-nm{font-family:"Noto Serif SC",serif;font-size:40px;font-weight:800}
#outro li .li-tag{font-size:26px;font-weight:600;color:#A9A091}
#outro li.top{border-color:rgba(242,205,115,.52);background:rgba(242,205,115,.08)}
#outro li.top .li-no,#outro li.top .li-nm{color:var(--gold)}
#cta{position:absolute;left:80px;right:80px;bottom:150px;z-index:32;text-align:center;opacity:0}
#cta .q1{font-size:46px;font-weight:900;color:var(--gold);line-height:1.25}
#cta .q2{margin-top:20px;font-size:34px;font-weight:800;color:var(--acc);letter-spacing:.16em}
'''


def video_tag(i, s):
    track = 0 if i % 2 == 0 else 6
    start = round(s["full_start"] - cfg.PREROLL, 3)
    d = round(cfg.PREROLL + s["show"], 3)
    return (f'<video id="fv_{s["key"]}" class="fv clip" data-start="{f(start)}" data-duration="{f(d)}" '
            f'data-track-index="{track}" src="clips_show/{s["key"]}.mp4" muted playsinline></video>')


def reveal_tag(i, s):
    col = GOLD if s["no"] == "01" else ACC
    d = round(s["full_start"] - cfg.PREROLL + 0.4 - s["start"], 3)
    return (f'''<div id="rv_{s['key']}" class="reveal clip" data-start="{f(s['start'])}" data-duration="{f(d)}" data-track-index="{20+i}">
  <div class="rv-ghost" id="rghost_{s['key']}">{s['no']}</div>
  <div class="rv-wrap">
    <div class="rv-rank" id="rr_{s['key']}" style="color:{col}">第 {int(s['no'])} 名</div>
    <div class="rv-rule" id="ru_{s['key']}" style="background:{col}"></div>
    <div class="rv-title" id="rt_{s['key']}">{s['title']}</div>
    <div class="rv-meta" id="rm_{s['key']}">{cfg.ARTIST} · {s['year']}　|　专辑《{s['album']}》</div>
    <div class="rv-tag" id="rtag_{s['key']}" style="color:{col}">{s['tag']}</div>
  </div>
</div>''')


def chip_tag(i, s):
    col = GOLD if s["no"] == "01" else ACC
    d = round(s["end"] - s["full_start"], 3)
    return (f'''<div id="chip_{s['key']}" class="chip clip" data-start="{f(s['full_start'])}" data-duration="{f(d)}" data-track-index="{30+i}">
  <div class="cno" style="color:{col}">{s['no']}</div><div class="cbar"></div>
  <div class="cnm">{s['title']}</div>
</div>''')


videos = "\n".join(video_tag(i, s) for i, s in enumerate(cfg.SONGS))
reveals = "\n".join(reveal_tag(i, s) for i, s in enumerate(cfg.SONGS))
chips = "\n".join(chip_tag(i, s) for i, s in enumerate(cfg.SONGS))

cover_html = f'''<div id="cover" class="clip" data-start="0" data-duration="{f(intro_end-0.1)}" data-track-index="2" style="--acc:{ACC}">
  <div class="cv-bg" data-layout-allow-overflow style="background-image:url('cover_assets/cover.jpg')"></div>
  <div class="cv-shade"></div>
  <div class="cv-wrap">
    <div class="cv-eyebrow">华语遗珠盘点</div>
    <div class="cv-h1">飞儿乐队<br>最被低估的<span class="em">5首歌</span></div>
    <div class="cv-sub">不是只有大热副歌。F.I.R. 的世界观，<br>也藏在那些没被所有人听见的歌里。</div>
    <div class="cv-chips"><span>史诗感</span><span>摇滚</span><span>信念</span><span>夜色</span><span>遗珠</span></div>
  </div>
</div>'''

recap_rows = "".join(
    f'<li class="{"top" if s["no"]=="01" else ""}" id="li_{s["key"]}"><div class="li-l">'
    f'<span class="li-no">{s["no"]}</span><span class="li-nm">{s["title"]}</span></div>'
    f'<span class="li-tag">{s["emo"]}</span></li>'
    for s in cfg.SONGS
)
outro_html = f'''<div id="outro" class="clip" data-start="{f(outro_start)}" data-duration="{f(TOTAL-outro_start)}" data-track-index="3" style="--acc:{ACC};--gold:{GOLD}">
  <div class="ot-small" id="ot_small">最终榜单 · 从第五到第一</div>
  <div class="ot-h" id="ot_h">飞儿被低估的，从来不是高音，<br>而是把流行、摇滚和远方，<br>写成一个完整世界的野心。</div>
  <ol>{recap_rows}</ol>
</div>
<div id="cta" class="clip" data-start="{f(cta_voice-0.25)}" data-duration="{f(TOTAL-cta_voice+0.25)}" data-track-index="4" style="--acc:{ACC};--gold:{GOLD}">
  <div class="q1">你最想为哪一首投票？</div>
  <div class="q2">点赞 · 收藏 · 关注</div>
</div>'''

audio_html = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="5" src="master.wav" data-volume="1"></audio>'


def js_song(i, s):
    k = s["key"]
    b = s["start"]
    fs = s["full_start"]
    fv0 = round(fs - cfg.PREROLL, 3)
    rv_end = round(fv0 + 0.4, 3)
    end = s["end"]
    fade = round(end - 1.2, 3)
    return f'''
// ---- {s['plain']} ----
tl.fromTo("#rv_{k}",{{opacity:0}},{{opacity:1,duration:.6,ease:"power2.out"}},{f(b)});
tl.fromTo("#rghost_{k}",{{opacity:0,scale:.92}},{{opacity:1,scale:1,duration:1.4,ease:"power3.out"}},{f(b+0.1)});
tl.fromTo("#rr_{k}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.6,ease:"expo.out"}},{f(b+0.5)});
tl.fromTo("#ru_{k}",{{width:0}},{{width:90,duration:.6,ease:"power2.out"}},{f(b+0.8)});
tl.fromTo("#rt_{k}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(b+1.0)});
tl.fromTo("#rm_{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.6,ease:"sine.out"}},{f(b+1.7)});
tl.fromTo("#rtag_{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{f(b+2.1)});
tl.to("#rv_{k}",{{opacity:0,duration:.6,ease:"power2.in"}},{f(rv_end-0.5)});
tl.set("#rv_{k}",{{opacity:0}},{f(rv_end)});
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.07}},{{opacity:1,scale:1,duration:{f(cfg.PREROLL*0.7)},ease:"power2.out"}},{f(fv0)});
tl.fromTo("#chip_{k}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.6,ease:"power2.out"}},{f(fs+0.2)});
tl.to("#chip_{k}",{{opacity:0,duration:.5,ease:"power1.in"}},{f(fade)});
tl.set("#chip_{k}",{{opacity:0}},{f(end)});
tl.to("#fv_{k}",{{opacity:0,duration:1.1,ease:"power1.in"}},{f(fade)});
tl.set("#fv_{k}",{{opacity:0}},{f(end)});
'''


outro_recap_js = "".join(
    f'tl.fromTo("#li_{s["key"]}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.45,ease:"power2.out"}},{f(outro_start+1.4+i*0.28)});'
    for i, s in enumerate(cfg.SONGS)
)

JS = f'''
tl.set("#cover",{{opacity:1}},0);
tl.to("#cover .cv-bg",{{scale:1.12,duration:{f(intro_end)},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.5,ease:"power1.in"}},{f(intro_end-0.5)});
tl.set("#cover",{{opacity:0}},{f(intro_end-0.05)});
{''.join(js_song(i,s) for i,s in enumerate(cfg.SONGS))}
// OUTRO
tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(outro_start-0.3)});
tl.fromTo("#ot_small",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.6,ease:"expo.out"}},{f(outro_start+0.4)});
tl.fromTo("#ot_h",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(outro_start+0.8)});
{outro_recap_js}
tl.fromTo("#cta",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.6,ease:"power2.out"}},{f(cta_voice-0.2)});
tl.to("#outro",{{opacity:1,duration:.1}},{f(TOTAL-0.2)});
'''

html = f'''<!doctype html>
<html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
{videos}
<div id="scrim" class="clip" data-start="0" data-duration="{f(TOTAL)}" data-track-index="1"></div>
{reveals}
{chips}
{cover_html}
{outro_html}
<div class="vig"></div>
<div id="grain"></div>
{audio_html}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script></body></html>'''

(HF / "index.html").write_text(html, encoding="utf-8")
(HF / "meta.json").write_text('{"id":"main","name":"fir-underrated-top5"}', encoding="utf-8")
print("index.html:", len(html), "bytes")

hits = sorted({w for w in cfg.FORBIDDEN if w in html})
if hits:
    raise SystemExit(f"!!! LEAK GUARD failed: index.html contains {hits}")
print("leak-guard CLEAN. BUILD DONE")
