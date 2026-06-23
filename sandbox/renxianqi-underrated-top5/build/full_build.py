#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 任贤齐最被低估的5首歌.

The final MP4 must be muxed with master.wav after HyperFrames render because
HyperFrames normalizes audio and flattens the intended ducking.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
CS = ROOT / "clips_seg"
CS.mkdir(exist_ok=True)

LEAD = 0.35
POST = 0.25
DIG = 1.35
BED = 0.17
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.05
OUTRO_TAIL = 2.8
DIGEST_O = 1.05
MASTER_GAIN = 1.03
VOCAL_PRE_ROLL = 2.0


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


items = [
    {
        "key": "p5_aishangle",
        "clip": "vert_p5_aishangle",
        "no": "05",
        "name": "《爱伤了》",
        "plain": "爱伤了",
        "meta": "老地方 · 2006",
        "show": 27.0,
        "ch_off": 180.72,
        "tag": "低调慢歌，伤到最后反而安静",
        "note": "不是江湖感，不靠大副歌硬砸，胜在情绪直接。",
    },
    {
        "key": "p4_yuedinglantian",
        "clip": "vert_p4_yuedinglantian",
        "no": "04",
        "name": "《约定蓝天》",
        "plain": "约定蓝天",
        "meta": "老地方 · 2006",
        "show": 12.0,
        "ch_off": 262.0,
        "align_vocal_to_narr_end": True,
        "tag": "苦情之外，还有一点往前看的明亮",
        "note": "《老地方》更出圈，这首更像中后期成熟温暖的侧面。",
    },
    {
        "key": "p3_xinqingchezhan",
        "clip": "vert_p3_xinqingchezhan",
        "no": "03",
        "name": "《心情车站》",
        "plain": "心情车站",
        "meta": "爱像太平洋 · 1998",
        "show": 26.5,
        "ch_off": 249.69,
        "tag": "不惊艳，却会慢慢留下来",
        "note": "像停在某个车站，把心情整理好，再继续往前走。",
    },
    {
        "key": "p2_bieku",
        "clip": "vert_p2_bie_ku",
        "no": "02",
        "name": "《别哭》",
        "plain": "别哭",
        "meta": "爱像太平洋 · 1998",
        "show": 36.0,
        "ch_off": 185.0,
        "align_vocal_to_narr_end": True,
        "tag": "不是大悲伤，是朴素地陪你",
        "note": "这首没有动态 MV 可用，本片采用可下载的高音质静态源。",
    },
    {
        "key": "p1_anjing",
        "clip": "vert_p1_an_jing_de_ren",
        "no": "01",
        "name": "《安静的人》",
        "plain": "安静的人",
        "meta": "爱像太平洋 · 1998",
        "show": 62.0,
        "ch_off": 211.9,
        "align_vocal_to_narr_end": True,
        "tag": "被超级大歌围住的内向一面",
        "note": "不争、不闹，把很多话放在心里，越重听越耐听。",
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
    full_start = q(narr_end + POST + DIG)
    end = q(full_start + item["show"])
    narr_end_local = q(narr_end - t)
    full_start_local = q(full_start - t)
    if item.get("align_vocal_to_narr_end"):
        vocal_start_local = q(max(0, narr_end_local - VOCAL_PRE_ROLL))
        mseek = q(max(0, item["ch_off"] - vocal_start_local))
    else:
        vocal_start_local = full_start_local
        mseek = q(max(0, item["ch_off"] - full_start_local))
    block = {
        **item,
        "start": q(t),
        "end": end,
        "narr_start": narr_start,
        "narr_end": narr_end,
        "vocal_start_local": vocal_start_local,
        "full_start": full_start,
        "full_start_local": full_start_local,
        "mseek": mseek,
        "seg_dur": q(end - t),
    }
    blocks.append(block)
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

intro_src = C / "vert_p3_xinqingchezhan.mp4"
intro_seek = 247.7
run(
    [
        "ffmpeg", "-v", "error", "-ss", str(intro_seek), "-i", str(intro_src), "-t", str(intro_end),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", str(CS / "intro.mp4"), "-y",
    ]
)
run(
    [
        "ffmpeg", "-v", "error",
        "-ss", str(intro_seek), "-i", str(intro_src),
        "-i", str(A / "intro.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.12,afade=t=in:st=0:d=0.7,afade=t=out:st={q(intro_end-0.8)}:d=0.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ]
)
segments.append("seg_intro.wav")

for block in blocks:
    src = C / f"{block['clip']}.mp4"
    seg = CS / f"{block['key']}.mp4"
    run(
        [
            "ffmpeg", "-v", "error", "-ss", str(block["mseek"]), "-i", str(src), "-t", str(block["seg_dur"]),
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
            "-c:a", "aac", "-b:a", "192k", str(seg), "-y",
        ]
    )
    narr_end_local = q(LEAD + block["voice_dur"])
    full_start_local = block["full_start_local"]
    env = envelope(narr_end_local, full_start_local)
    out = f"seg_{block['key']}.wav"
    run(
        [
            "ffmpeg", "-v", "error",
            "-i", str(seg),
            "-i", str(A / f"{block['key']}.wav"),
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{block['seg_dur']},volume='{env}':eval=frame[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
outro_src = C / "vert_p1_an_jing_de_ren.mp4"
outro_seek = 193.0
run(
    [
        "ffmpeg", "-v", "error", "-ss", str(outro_seek), "-i", str(outro_src), "-t", str(outro_dur),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", str(CS / "outro.mp4"), "-y",
    ]
)
run(
    [
        "ffmpeg", "-v", "error",
        "-ss", str(outro_seek), "-i", str(outro_src),
        "-i", str(A / "outro.wav"),
        "-i", str(A / "outro_cta.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.16,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ]
)
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(
    [
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
        "-af", f"volume={MASTER_GAIN},alimiter=limit=0.97",
        "-ac", "2", "-ar", "48000", "master.wav", "-y",
    ]
)
print("master dur:", dur(ROOT / "master.wav"), "planned:", total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="{src}" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, "clips_seg/intro.mp4")]
for idx, block in enumerate(blocks, start=1):
    videos.append(video_tag(idx, block["start"], block["seg_dur"], f"clips_seg/{block['key']}.mp4"))
videos.append(video_tag(len(videos), outro_start, outro_dur, "clips_seg/outro.mp4"))

labels = []
tweens = []
for idx, block in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(block["full_start"] - block["start"])
    mdur = q(block["end"] - block["full_start"])
    top = " topRank" if block["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{top}" data-start="{block["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {block["no"]} 名</div><div class="meta">{block["meta"]}</div><h2>{block["name"]}</h2>'
        f'<p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{top}" data-start="{block["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{block["no"]}</span><strong>{block["plain"]}</strong></section>'
    )
    s = block["start"]
    fs = block["full_start"]
    e = block["end"]
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(s+.18)});')
    tweens.append(f'tl.fromTo("#{fid} .meta",{{x:-22,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"sine.out"}},{q(s+.34)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:46,opacity:0}},{{y:0,opacity:1,duration:.64,ease:"power3.out"}},{q(s+.5)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power1.out"}},{q(s+.86)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+1.12)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(fs-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(fs)});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(fs+.1)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(e-.35)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{q(e)});')

transition_divs = []
transition_tweens = []
for i, block in enumerate(blocks):
    tid = f"tr{i}"
    ts = q(max(0, block["start"] - 0.15))
    transition_divs.append(
        f'<div id="{tid}" class="clip trans" data-start="{ts}" data-duration="0.9" data-track-index="8"></div>'
    )
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.58,scaleY:.05}},{{opacity:0,scaleY:1,duration:.75,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "爱伤了"),
        ("04", "约定蓝天"),
        ("03", "心情车站"),
        ("02", "别哭"),
        ("01", "安静的人"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08100f;
  font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif;color:#f5f0e4;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08100f}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,15,14,.86),rgba(6,15,14,.13) 31%,rgba(6,15,14,.20) 58%,rgba(5,10,10,.90))}
#aurora{position:absolute;inset:-260px;z-index:1;opacity:.40;background:radial-gradient(48% 30% at 18% 18%,rgba(94,168,143,.46),rgba(94,168,143,0) 64%),radial-gradient(54% 32% at 84% 80%,rgba(222,174,92,.30),rgba(222,174,92,0) 66%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.08;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(245,240,228,.13) 0 1px,transparent 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(222,174,92,0),rgba(222,174,92,.76),rgba(94,168,143,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:132px 78px 132px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(6,15,14,.82),rgba(6,15,14,.22) 34%,rgba(6,15,14,.18) 60%,rgba(5,10,10,.90))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#5ea88f;letter-spacing:.12em}
.eyebrow:before{content:"";width:58px;height:4px;background:#5ea88f;border-radius:99px;box-shadow:0 0 18px rgba(94,168,143,.70)}
#cover h1{margin-top:30px;font-family:"Noto Serif SC",serif;font-size:112px;line-height:1.1;font-weight:900;max-width:940px;text-shadow:0 6px 42px rgba(0,0,0,.64)}
#cover h1 b{color:#deae5c;font-weight:900}
#cover .sub{margin-top:30px;font-size:37px;line-height:1.52;color:#d7ded9;font-weight:600;max-width:900px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:930px}
.chips span{border:1.5px solid rgba(94,168,143,.58);color:#ddf0e8;background:rgba(6,15,14,.58);font-size:28px;font-weight:800;padding:12px 20px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(6,15,14,.90),rgba(6,15,14,.52));border-left:8px solid #5ea88f;border-radius:5px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.26)}
.fullLabel .rank{font-size:31px;font-weight:900;color:#5ea88f;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#becbc4;letter-spacing:.08em}
.fullLabel h2{font-family:"Noto Serif SC",serif;margin-top:12px;font-size:76px;line-height:1.12;font-weight:900;color:#fff}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#deae5c}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#d5ddd9}
.fullLabel.topRank{border-left-color:#deae5c;background:linear-gradient(135deg,rgba(16,12,9,.92),rgba(7,13,12,.54))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#deae5c}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(6,15,14,.70);border:1.5px solid rgba(94,168,143,.62);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:900;color:#5ea88f}
.miniLabel strong{font-family:"Noto Serif SC",serif;font-size:36px;font-weight:900;max-width:800px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(222,174,92,.78)}
.miniLabel.topRank span{color:#deae5c}
#outro{position:absolute;z-index:5;inset:0;padding:118px 72px 160px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(6,15,14,.34),rgba(5,10,10,.84))}
#outro .small{font-size:31px;font-weight:900;color:#5ea88f;letter-spacing:.14em}
#outro h2{font-family:"Noto Serif SC",serif;margin-top:20px;font-size:62px;line-height:1.22;font-weight:900;max-width:925px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 22px;background:rgba(6,15,14,.64);border:1px solid rgba(245,240,228,.14);border-radius:8px}
#outro li span{font-size:32px;font-weight:900;color:#5ea88f}
#outro li:last-child{background:rgba(222,174,92,.14);border-color:rgba(222,174,92,.44)}
#outro li:last-child span{color:#deae5c}
#outro li strong{font-family:"Noto Serif SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:32px;font-size:30px;line-height:1.52;color:#d7ded9;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px 20px;background:rgba(6,15,14,.72);border:1.5px solid rgba(222,174,92,.42);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#deae5c;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#5ea88f;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="aurora" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 小齐内向面</div><h1>任贤齐<br><b>最被低估</b>的5首歌</h1>'
    '<p class="sub">那些国民级大歌之外，还有更沉、更温柔、更不热闹的一面。真爱粉重听，会发现它们一直在。</p></div>'
    '<div class="chips"><span>倒数揭晓</span><span>专辑遗珠</span><span>爱像太平洋</span><span>老地方</span><span>安静情歌</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>任贤齐不只有热闹的大歌，也有沉默、安慰、停顿和重新出发。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：爱伤了、约定蓝天、心情车站、别哭、安静的人。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.018,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.25);
tl.fromTo("#aurora",{{x:-18,y:0}},{{x:20,y:-14,duration:{total},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.42,ease:"power1.in"}},{q(intro_end-.5)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(transition_tweens)}
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.18)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(outro_start+2.18)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power1.out"}},{q(cta_voice+.35)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "renxianqi-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], b["mseek"]) for b in blocks])
