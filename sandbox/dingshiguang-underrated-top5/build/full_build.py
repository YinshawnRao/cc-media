#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 丁世光最被低估的5首歌.

Final render must be muxed with master.wav after HyperFrames render.
"""
import contextlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
AUDIO = ROOT / "audio"
CLIPS = ROOT / "clips_seg"
CLIPS.mkdir(exist_ok=True)

HTML_ONLY = os.environ.get("HTML_ONLY") == "1"

LEAD = 0.35
POST = 0.25
DIG = 1.45
BED = 0.16
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.15
OUTRO_TAIL = 2.8
DIGEST_O = 1.05
MASTER_GAIN = 1.03


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run([str(c) for c in cmd], cwd=ROOT, check=True)


def vert_filter(crop, br=0.0, sat=1.0):
    return (
        f"[0:v]crop={crop},split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=30,eq=brightness={br}:saturation={sat}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


NARR_FILE = {
    "p5": "p5_wutuobang",
    "p4": "p4_nidejia",
    "p3": "p3_yueshi",
    "p2": "p2_ruguo",
    "p1": "p1_busandeyanxi",
}

ITEMS = [
    {
        "key": "p5", "no": "05", "src_key": "p5_wutuobang", "src": "p5_wutuobang.mp4",
        "name": "《乌托邦》", "plain": "乌托邦", "meta": "Utopia · 官方视频",
        "show": 25.8, "ch_off": 146.2, "crop": "1920:820:0:140", "br": 0.03, "sat": 1.08,
        "tag": "明亮、异域、带一点逃离现实感",
        "note": "不走常规抒情路线，却证明他的审美不窄",
    },
    {
        "key": "p4", "no": "04", "src_key": "p4_nidejia", "src": "p4_nidejia.mp4",
        "name": "《你的家》", "plain": "你的家", "meta": "Your Home · 官方视频",
        "show": 38.5, "ch_off": 122.8, "crop": "1920:820:0:140", "br": 0.02, "sat": 1.03,
        "tag": "长大以后，才听懂沉默里的重量",
        "note": "安静到不容易传播，却有很厚的生活感",
    },
    {
        "key": "p3", "no": "03", "src_key": "p3_yueshi_live", "src": "p3_yueshi_live.mp4",
        "name": "《月食》", "plain": "月食", "meta": "The Weeping Woman · 蓝巡现场",
        "show": 35.7, "ch_off": 192.0, "crop": "1920:900:0:80", "br": 0.01, "sat": 1.12,
        "tag": "两个人的光，一点点被挡住",
        "note": "氛围完整，像一段慢慢变暗的镜头",
    },
    {
        "key": "p2", "no": "02", "src_key": "p2_if_live", "src": "p2_if_live.mp4",
        "name": "《如果我们当时一起会怎么样》", "plain": "如果我们当时一起会怎么样", "meta": "If · 现场版",
        "show": 38.0, "ch_off": 170.0, "crop": "1920:900:0:100", "br": 0.02, "sat": 1.08,
        "tag": "不是哭诉分开，而是在想另一条人生线",
        "note": "被更易记的歌盖住，却更适合深夜反复听",
        "long": True,
    },
    {
        "key": "p1", "no": "01", "src_key": "p1_busan_live", "src": "p1_busan_live.mp4",
        "name": "《不散的筵席》", "plain": "不散的筵席", "meta": "I Miss You · 蓝巡深圳现场",
        "show": 34.3, "ch_off": 28.0, "crop": "1920:820:0:160", "br": 0.02, "sat": 1.08,
        "tag": "把离别唱得体面、克制、有后劲",
        "note": "像电影散场后，还留在座位上的人",
    },
]

for item in ITEMS:
    item["voice_dur"] = dur(AUDIO / f"{NARR_FILE[item['key']]}.wav")

d_intro = dur(AUDIO / "intro.wav")
d_outro = dur(AUDIO / "outro.wav")
d_cta = dur(AUDIO / "outro_cta.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in ITEMS:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + POST + DIG)
    end = q(full_start + item["show"])
    full_start_local = q(full_start - t)
    mseek = q(max(0.0, item["ch_off"] - full_start_local))
    block = {
        **item,
        "start": q(t), "end": end,
        "narr_start": narr_start, "narr_end": narr_end,
        "full_start": full_start, "full_start_local": full_start_local,
        "mseek": mseek, "seg_dur": q(end - t),
        "clip": item["src_key"],
    }
    blocks.append(block)
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)
outro_dur = q(total - outro_start)

sys.path.insert(0, str(ROOT.parents[1]))
from tools.video import showcase_align  # noqa: E402

showcase_align.gate(
    blocks,
    ROOT / "probe" / "vocal_final_raw.json",
    consts=dict(POST=POST, DIG=DIG),
    plan_path=ROOT / "probe" / "showcase_plan.json",
)

segments = []

first = blocks[0]
intro_mseek = q(max(0.0, first["mseek"] - intro_end))
last = blocks[-1]
outro_mseek = q(min(260.0, last["mseek"] + last["seg_dur"]))

if not HTML_ONLY:
    run([
        "ffmpeg", "-v", "error", "-ss", intro_mseek, "-i", RAW / first["src"],
        "-t", intro_end, "-filter_complex", vert_filter(first["crop"], first["br"], first["sat"]),
        "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
        CLIPS / "intro.mp4", "-y",
    ])
    run([
        "ffmpeg", "-v", "error",
        "-ss", intro_mseek, "-i", RAW / first["src"],
        "-i", AUDIO / "intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.13,afade=t=in:st=0:d=0.7,afade=t=out:st={q(intro_end-0.8)}:d=0.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ])
segments.append("seg_intro.wav")

for block in blocks:
    if not HTML_ONLY:
        run([
            "ffmpeg", "-v", "error", "-ss", block["mseek"], "-i", RAW / block["src"],
            "-t", block["seg_dur"], "-filter_complex", vert_filter(block["crop"], block["br"], block["sat"]),
            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
            CLIPS / f"{block['key']}.mp4", "-y",
        ])
        narr_end_local = q(LEAD + block["voice_dur"])
        env = envelope(narr_end_local, block["full_start_local"])
        run([
            "ffmpeg", "-v", "error",
            "-ss", block["mseek"], "-i", RAW / block["src"],
            "-i", AUDIO / f"{NARR_FILE[block['key']]}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{block['seg_dur']},volume='{env}':eval=frame[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=level=disabled:limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", f"seg_{block['key']}.wav", "-y",
        ])
    segments.append(f"seg_{block['key']}.wav")

if not HTML_ONLY:
    run([
        "ffmpeg", "-v", "error", "-ss", outro_mseek, "-i", RAW / last["src"],
        "-t", outro_dur, "-filter_complex", vert_filter(last["crop"], last["br"], last["sat"]),
        "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
        CLIPS / "outro.mp4", "-y",
    ])
    cta_local = q(cta_voice - outro_start)
    run([
        "ffmpeg", "-v", "error",
        "-ss", outro_mseek, "-i", RAW / last["src"],
        "-i", AUDIO / "outro.wav",
        "-i", AUDIO / "outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.18,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ])
segments.append("seg_outro.wav")

if not HTML_ONLY:
    video_list = ["clips_seg/intro.mp4"] + [f"clips_seg/{b['key']}.mp4" for b in blocks] + ["clips_seg/outro.mp4"]
    (ROOT / "footage_seglist.txt").write_text("".join(f"file '{name}'\n" for name in video_list), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "footage_seglist.txt",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
        "-an", CLIPS / "footage_track.mp4", "-y",
    ])
    (ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
        "-af", f"volume={MASTER_GAIN},alimiter=level=disabled:limit=0.97",
        "-ac", "2", "-ar", "48000", "master.wav", "-y",
    ])
    print("master dur:", dur(ROOT / "master.wav"), "planned:", total)

videos = [
    f'<video id="v0" class="clip fv" data-start="0" data-duration="{total}" '
    f'data-track-index="0" src="clips_seg/footage_track.mp4" muted playsinline></video>'
]

labels = []
tweens = []
for idx, block in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(block["full_start"] - block["start"])
    mdur = q(block["end"] - block["full_start"])
    top = " topRank" if block["no"] == "01" else ""
    long = " longTitle" if block.get("long") else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{top}{long}" data-start="{block["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {block["no"]} 名</div><div class="meta">{block["meta"]}</div><h2>{block["name"]}</h2>'
        f'<p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{top}{long}" data-start="{block["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{block["no"]}</span><strong>{block["plain"]}</strong></section>'
    )
    s, fs, e = block["start"], block["full_start"], block["end"]
    tweens.extend([
        f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(s+.18)});',
        f'tl.fromTo("#{fid} .meta",{{x:-22,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"sine.out"}},{q(s+.34)});',
        f'tl.fromTo("#{fid} h2",{{y:46,opacity:0}},{{y:0,opacity:1,duration:.64,ease:"power3.out"}},{q(s+.5)});',
        f'tl.fromTo("#{fid} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power1.out"}},{q(s+.9)});',
        f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+1.18)});',
        f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(fs-.4)});',
        f'tl.set("#{fid}",{{opacity:0}},{q(fs)});',
        f'tl.fromTo("#{mid}",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(fs+.1)});',
        f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(e-.35)});',
        f'tl.set("#{mid}",{{opacity:0}},{q(e)});',
    ])

transition_divs = []
transition_tweens = []
for i, block in enumerate(blocks):
    tid = f"tr{i}"
    ts = q(max(0, block["start"] - 0.15))
    transition_divs.append(
        f'<div id="{tid}" class="clip trans" data-start="{ts}" data-duration="0.9" data-track-index="8"></div>'
    )
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.54,scaleY:.04}},{{opacity:0,scaleY:1,duration:.78,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "乌托邦"),
        ("04", "你的家"),
        ("03", "月食"),
        ("02", "如果我们当时一起会怎么样"),
        ("01", "不散的筵席"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06070a;font-family:"PingFang SC",system-ui,sans-serif;color:#eef0f4;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#06070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,7,10,.90),rgba(6,7,10,.08) 30%,rgba(6,7,10,.20) 58%,rgba(5,5,8,.94))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.34;background:radial-gradient(42% 26% at 18% 16%,rgba(226,176,82,.34),rgba(226,176,82,0) 66%),radial-gradient(48% 30% at 84% 82%,rgba(88,168,190,.26),rgba(88,168,190,0) 70%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.052;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(238,240,244,.13) 0 1px,rgba(238,240,244,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(226,176,82,0),rgba(226,176,82,.46),rgba(88,168,190,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:120px 76px 116px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(6,7,10,.82),rgba(6,7,10,.10) 30%,rgba(6,7,10,.22) 60%,rgba(5,5,8,.92))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#e6bd73;letter-spacing:.10em}
.eyebrow:before{content:"";width:58px;height:4px;background:#e6bd73;border-radius:99px;box-shadow:0 0 18px rgba(230,189,115,.55)}
#cover h1{margin-top:28px;font-family:"Songti SC",serif;font-size:104px;line-height:1.1;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.70)}
#cover h1 b{color:#f1d28d;font-weight:900}
#cover .sub{margin-top:556px;font-size:35px;line-height:1.5;color:#d8dbe1;font-weight:650;max-width:920px;text-shadow:0 3px 20px rgba(0,0,0,.82)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(230,189,115,.46);color:#e9ecf0;background:rgba(6,7,10,.56);font-size:27px;font-weight:850;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(6,7,10,.91),rgba(25,23,18,.58));border-left:8px solid #d49b48;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.36)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e6bd73;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:750;color:#b8b5ac;letter-spacing:.04em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:80px;line-height:1.12;font-weight:900;color:#eef0f4}
.fullLabel.longTitle h2{font-size:56px;line-height:1.18}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#f1d28d}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:650;color:#d8dbe1}
.fullLabel.topRank{border-left-color:#f0d488;background:linear-gradient(135deg,rgba(18,14,8,.93),rgba(6,7,10,.60))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f0d488}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(6,7,10,.70);border:1.5px solid rgba(230,189,115,.48);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#eef0f4;background:#06070a;border:1px solid rgba(230,189,115,.48);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.longTitle strong{font-size:29px;max-width:820px}
.miniLabel.topRank{border-color:rgba(240,212,136,.76)}
.miniLabel.topRank span{border-color:rgba(240,212,136,.70)}
#outro{position:absolute;z-index:5;inset:0;padding:110px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(6,7,10,.42),rgba(6,7,10,.90))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e6bd73;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:54px;line-height:1.3;font-weight:900;max-width:936px}
#outro ol{margin-top:34px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(6,7,10,.64);border:1px solid rgba(238,240,244,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#eef0f4;background:#06070a;border:1px solid rgba(230,189,115,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(240,212,136,.14);border-color:rgba(240,212,136,.45)}
#outro li:last-child span{border-color:rgba(240,212,136,.65)}
#outro li strong{font-family:"Songti SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro li:nth-child(4) strong{font-size:27px}
#outro .close{margin-top:28px;font-size:30px;line-height:1.5;color:#d8dbe1;font-weight:650}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px;background:rgba(6,7,10,.72);border:1.5px solid rgba(240,212,136,.42);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f0d488;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#7fc9da;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">不只神经志 · 低估遗珠</div><h1>丁世光<br><b>最被低估</b>的5首歌</h1></div>'
    '<div><p class="sub">有些歌不靠爆点，也不靠情绪抓马，却能在听完之后慢慢回来。这五首，藏着丁世光最克制、也最有后劲的一面。</p>'
    '<div class="chips" style="margin-top:26px"><span>R&B审美</span><span>离别后劲</span><span>听觉电影感</span><span>安静亲情</span><span>浪漫逃离</span></div></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>丁世光最被低估的，不只是某一首歌没红，而是他总能把复杂情绪唱得很轻，却让后劲留得很久。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这些不喧哗的作品，刚好拼出一个更完整的丁世光。</p></section>'
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
tl.fromTo("#glow",{{x:-18,y:0}},{{x:20,y:-14,duration:{total},ease:"none"}},0);
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
(ROOT / "meta.json").write_text(json.dumps({
    "id": "main",
    "name": "dingshiguang-underrated-top5",
    "total": total,
    "intro_end": intro_end,
    "outro_start": outro_start,
    "intro_mseek": intro_mseek,
    "outro_mseek": outro_mseek,
    "blocks": [
        {
            "no": b["no"], "plain": b["plain"], "src": b["src"], "src_key": b["src_key"],
            "start": b["start"], "narr_start": b["narr_start"], "narr_end": b["narr_end"],
            "full_start": b["full_start"], "end": b["end"], "mseek": b["mseek"],
            "ch_off": b["ch_off"], "show": b["show"], "crop": b["crop"],
        }
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"]) for b in blocks])
