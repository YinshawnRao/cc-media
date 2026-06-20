#!/usr/bin/env python3
"""Build clips, master.wav and HyperFrames HTML for 王菲最难的5首歌."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
R = ROOT / "raw"

LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
OUTRO_TAIL = 2.6
DIGEST_O = 1.0


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


def ensure_audio(src, out):
    run([
        "ffmpeg", "-v", "error", "-i", str(src), "-vn",
        "-ac", "2", "-ar", "48000", str(out), "-y",
    ])


def make_vert(src, out, start, length, crop):
    """Create 1080x1920 letterbox vertical clip from a source time window."""
    vf = (
        f"crop={crop},split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,gblur=sigma=30,eq=brightness=-0.34:saturation=1.04[bgb];"
        "[fg]scale=1080:-2[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run([
        "ffmpeg", "-v", "error", "-ss", str(start), "-t", str(length),
        "-i", str(src), "-filter_complex", vf, "-map", "[v]",
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
        "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
        "-an", str(out), "-y",
    ])


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

items = [
    {
        "key": "p5_kaidao",
        "clip": "vert_kaidao",
        "audio": "kaidao_audio.wav",
        "src": "kaidao_show.mp4",
        "src_start": 0.0,
        "music_s0": 89.0,
        "crop": "1418:870:246:0",
        "show": 36.0,
        "no": "05",
        "name": "《开到荼蘼》",
        "plain": "开到荼蘼",
        "tag": "冷、倔、锋利之间的平衡",
        "note": "副歌有推力但不能吼，锋芒不能显得用力",
    },
    {
        "key": "p4_bianhua",
        "clip": "vert_bianhua",
        "audio": "bianhua_audio.wav",
        "src": "bianhua_show.mp4",
        "src_start": 0.0,
        "music_s0": 149.0,
        "crop": "1920:720:0:175",
        "show": 36.0,
        "no": "04",
        "name": "《彼岸花》",
        "plain": "彼岸花",
        "tag": "越轻越难有支点",
        "note": "长线条、宿命感、气息和尾音都要干净",
    },
    {
        "key": "p3_hanwuji",
        "clip": "vert_hanwuji",
        "audio": "hanwuji_audio.wav",
        "src": "hanwuji_full.mp4",
        "src_start": 216.7,
        "music_s0": 216.7,
        "crop": "1096:500:0:0",
        "show": 34.0,
        "no": "03",
        "name": "《寒武纪》",
        "plain": "寒武纪",
        "tag": "难在克制，难在唱对",
        "note": "冷、悬、远，情绪不能太满也不能空掉",
    },
    {
        "key": "p2_duodeta",
        "clip": "vert_duodeta",
        "audio": "duodeta_audio.wav",
        "src": "duodeta_full.mp4",
        "src_start": 190.0,
        "music_s0": 190.0,
        "crop": "1920:980:0:0",
        "show": 36.0,
        "no": "02",
        "name": "《多得他》",
        "plain": "多得他",
        "tag": "R and B 律动和气息弹性",
        "note": "每一句都要有 groove，轻盈但不能薄",
    },
    {
        "key": "p1_face",
        "clip": "vert_face",
        "audio": "face_audio.wav",
        "src": "face_susie.mp4",
        "src_start": 126.0,
        "music_s0": 126.0,
        "crop": "640:480:0:0",
        "show": 38.0,
        "no": "01",
        "name": "《脸》",
        "plain": "脸",
        "tag": "类美声腔体，但不能学院派",
        "note": "圆、厚、立体，还要保留轻、冷、飘",
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")
for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")

C.mkdir(parents=True, exist_ok=True)
ensure_audio(R / "face_susie.mp4", R / "face_audio.wav")
ensure_audio(R / "duodeta_full.mp4", R / "duodeta_audio.wav")
ensure_audio(R / "hanwuji_full.mp4", R / "hanwuji_audio.wav")
for item in items:
    make_vert(R / item["src"], C / f"{item['clip']}.mp4", item["src_start"], item["show"], item["crop"])

intro_end = q(INTRO_VOICE_START + d_intro + 0.9)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + item["show"] + 0.65)
    music_offset = q(item["music_s0"] - (full_start - t))
    if music_offset < 0:
        raise RuntimeError(f"{item['key']} music_offset < 0")
    block = {
        **item,
        "start": q(t),
        "end": end,
        "narr_start": narr_start,
        "narr_end": narr_end,
        "full_start": full_start,
        "music_offset": music_offset,
    }
    blocks.append(block)
    t = q(end)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
planned_total = q(cta_voice_end + OUTRO_TAIL)


def song_envelope(narr_end_local, full_start_local, show_end_local, seg_dur):
    swell = q(narr_end_local + 0.25)
    fade_start = q(show_end_local)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(between(t,{full_start_local},{fade_start}))*1.0"
        f"+(gte(t,{fade_start}))*max(0,1.0-1.0*(t-{fade_start})/{q(seg_dur-fade_start)})"
    )


segments = []

intro_dur = intro_end
run([
    "ffmpeg", "-v", "error",
    "-i", f"{R}/face_audio.wav",
    "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]atrim=8:{q(8+intro_dur)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={q(intro_dur-0.8)}:d=0.8[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    show_end_local = q(full_start_local + b["show"])
    env = song_envelope(narr_end_local, full_start_local, show_end_local, seg_dur)
    out = f"seg_{b['key']}.wav"
    run([
        "ffmpeg", "-v", "error",
        "-i", f"{R}/{b['audio']}",
        "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]atrim={b['music_offset']}:{q(b['music_offset']+seg_dur)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,volume='{env}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

outro_dur = q(planned_total - outro_start)
cta_local = q(cta_voice - outro_start)
run([
    "ffmpeg", "-v", "error",
    "-i", f"{R}/face_audio.wav",
    "-i", f"{A}/outro.wav",
    "-i", f"{A}/outro_cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]atrim=126:{q(126+outro_dur)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,volume=0.13,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.6)}:d=1.6[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, block):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{block["full_start"]}" '
        f'data-duration="{block["show"]}" data-track-index="{track}" '
        f'src="clips/{block["clip"]}.mp4" muted playsinline></video>'
    )


videos = [video_tag(i, b) for i, b in enumerate(blocks)]

cards = []
minis = []
tweens = []
for i, b in enumerate(blocks):
    card_dur = q(b["full_start"] - b["start"])
    rank_class = " topRank" if b["no"] == "01" else ""
    cards.append(
        f'<section id="card{i}" class="clip rankCard{rank_class}" data-start="{b["start"]}" '
        f'data-duration="{card_dur}" data-track-index="{2 + (i % 2)}">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2>'
        f'<p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>'
    )
    minis.append(
        f'<section id="mini{i}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" '
        f'data-duration="{b["show"]}" data-track-index="{4 + (i % 2)}">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>'
    )
    t0 = q(b["start"] + 0.18)
    tweens.append(f'tl.fromTo("#card{i} .rank",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.45}},{t0});')
    tweens.append(f'tl.fromTo("#card{i} h2",{{y:42,opacity:0}},{{y:0,opacity:1,duration:.60}},{q(t0+.18)});')
    tweens.append(f'tl.fromTo("#card{i} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45}},{q(t0+.55)});')
    tweens.append(f'tl.fromTo("#card{i} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.45}},{q(t0+.78)});')
    tweens.append(f'tl.fromTo("#v{i}",{{opacity:0}},{{opacity:1,duration:.55}},{q(b["full_start"])});')
    tweens.append(f'tl.fromTo("#mini{i}",{{x:-24,opacity:0}},{{x:0,opacity:1,duration:.45}},{q(b["full_start"]+.12)});')

ranking_rows = "".join(
    f'<li><span>{b["no"]}</span><strong>{b["plain"]}</strong></li>'
    for b in reversed(blocks)
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080d;font-family:"PingFang SC","Hiragino Sans GB","Songti SC",serif;color:#f8f4ed}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07080d}
#backdrop{position:absolute;inset:0;z-index:0;background:
radial-gradient(circle at 20% 14%,rgba(184,63,74,.35),rgba(184,63,74,0) 36%),
radial-gradient(circle at 74% 34%,rgba(16,45,49,.55),rgba(16,45,49,0) 42%),
linear-gradient(180deg,#07080d,#090a10 56%,#050509)}
#ghost{position:absolute;z-index:1;right:20px;bottom:78px;width:980px;font-size:158px;line-height:.86;font-weight:950;color:rgba(248,244,237,.045);letter-spacing:0;text-align:right}
#scrim{position:absolute;inset:0;z-index:3;background:linear-gradient(to bottom,rgba(5,6,10,.72),rgba(5,6,10,.15) 35%,rgba(5,6,10,.18) 61%,rgba(5,6,10,.86))}
#grain{position:absolute;inset:-30px;z-index:8;opacity:.11;background:repeating-linear-gradient(0deg,rgba(255,255,255,.16) 0 1px,transparent 1px 4px);mix-blend-mode:overlay;pointer-events:none}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:2;opacity:0}
#cover{position:absolute;z-index:5;inset:0;padding:158px 72px 148px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:31px;font-weight:850;color:#d8b56a}
.eyebrow:before{content:"";width:54px;height:4px;background:#d8b56a;border-radius:99px}
#cover h1{margin-top:30px;font-size:130px;line-height:1.04;font-weight:950;max-width:900px;letter-spacing:0}
#cover .sub{margin-top:28px;font-size:38px;line-height:1.45;color:#d4cbc1;font-weight:650;max-width:900px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(216,181,106,.55);color:#f0d9a8;background:rgba(7,8,13,.56);font-size:28px;font-weight:760;padding:12px 18px;border-radius:8px}
.rankCard{position:absolute;z-index:5;left:68px;right:68px;bottom:178px;padding:35px 34px 38px;background:linear-gradient(135deg,rgba(7,8,13,.88),rgba(7,8,13,.54));border-left:8px solid #d8b56a}
.rankCard .rank{font-size:31px;font-weight:900;color:#d8b56a}
.rankCard h2{margin-top:14px;font-size:86px;line-height:1.05;font-weight:950;letter-spacing:0}
.rankCard .tag{margin-top:18px;font-size:40px;line-height:1.28;font-weight:850;color:#d8b56a}
.rankCard .note{margin-top:12px;font-size:31px;line-height:1.38;font-weight:650;color:#d1c7bd}
.rankCard.topRank{border-left-color:#b83f4a}
.rankCard.topRank .rank,.rankCard.topRank .tag{color:#ff7683}
.miniLabel{position:absolute;z-index:6;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(7,8,13,.76);border:1px solid rgba(216,181,106,.62);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:950;color:#d8b56a}
.miniLabel strong{font-size:38px;font-weight:900}
.miniLabel.topRank{border-color:rgba(184,63,74,.86)}
.miniLabel.topRank span{color:#ff7683}
#outro{position:absolute;z-index:5;inset:0;padding:150px 72px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#d8b56a}
#outro h2{margin-top:18px;font-size:66px;line-height:1.16;font-weight:950;max-width:920px;letter-spacing:0}
#outro ol{margin-top:44px;list-style:none;display:grid;gap:16px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(7,8,13,.66);border:1px solid rgba(255,255,255,.13);border-radius:8px}
#outro li span{font-size:34px;font-weight:950;color:#d8b56a}
#outro li:first-child span{color:#ff7683}
#outro li strong{font-size:35px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:31px;line-height:1.45;color:#d4cbc1;font-weight:650}
#cta{position:absolute;z-index:7;left:76px;right:76px;bottom:96px;text-align:center;padding:24px 18px;background:rgba(7,8,13,.76);border:1px solid rgba(216,181,106,.36);border-radius:8px}
#cta .v{font-size:45px;font-weight:950;color:#ff7683;line-height:1.2}
#cta .f{margin-top:16px;font-size:36px;font-weight:850;color:#d8b56a;letter-spacing:0}
"""

body = '<div id="backdrop"></div><div id="ghost">FAYE<br>WONG</div>'
body += "\n" + "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="11"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{intro_end}" data-track-index="2">'
    '<div><div class="eyebrow">声乐难度盘点</div><h1>王菲最难的5首歌</h1>'
    '<p class="sub">不只看高音。真正难的是音准、气息、共鸣、律动，以及那种轻到快消失、却稳稳落地的控制力。</p></div>'
    '<div class="chips"><span>音准控制</span><span>腔体共鸣</span><span>R and B 律动</span><span>寓言感</span><span>冷感锋芒</span></div></section>'
)
body += "\n" + "\n".join(cards)
body += "\n" + "\n".join(minis)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>王菲最难的地方，是她看起来很轻，其实每一个音都站得很稳。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：开到荼蘼、彼岸花、寒武纪、多得他、脸。越往前，越不是靠模仿空灵能唱出来的难。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="12" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.fromTo("#cover .eyebrow",{{x:-24,opacity:0}},{{x:0,opacity:1,duration:.55}},0.35);
tl.fromTo("#cover h1",{{y:52,opacity:0}},{{y:0,opacity:1,duration:.75}},0.65);
tl.fromTo("#cover .sub",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.55}},1.15);
tl.fromTo("#cover .chips span",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.45,stagger:.08}},1.55);
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.65}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,stagger:.1}},{q(outro_start+1.15)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45}},{q(outro_start+2.0)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5}},{q(cta_voice+0.35)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="vendor/gsap-lite.js"></script>
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "wangfei-hardest-top5"}, ensure_ascii=False), encoding="utf-8")
(ROOT / "timeline.json").write_text(json.dumps({
    "total": total,
    "intro_end": intro_end,
    "outro_start": outro_start,
    "cta_voice": cta_voice,
    "blocks": [
        {
            "key": b["key"],
            "no": b["no"],
            "name": b["plain"],
            "start": b["start"],
            "full_start": b["full_start"],
            "show_end": q(b["full_start"] + b["show"]),
            "end": b["end"],
            "music_offset": b["music_offset"],
        }
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], b["music_offset"]) for b in blocks])
