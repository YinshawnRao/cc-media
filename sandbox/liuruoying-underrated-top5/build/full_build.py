#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 刘若英最被低估的5首歌.

Countdown 5 -> 1 (#1 = 打了一把钥匙给你, the climax). COUPLED audio: every song's
footage AND music come from the SAME source window (official MV / clean Live), so the
showcase chorus lip-syncs. Per segment both video (clips_seg/<key>.mp4) and music
(raw/<key>_aud.wav, extracted from the same vert clip) are sliced from `mseek` so the
chorus (ch_off, vert-local time) lands at the full-volume showcase start.

All album/year on screen are web-verified (brief had several wrong):
  我曾爱过一个男孩=我等你2000 · 阁楼=到处乱走1996 · 透明=很爱很爱你1998 ·
  点亮橘子树=年华2001 · 打了一把钥匙给你=雨季1995.

Final audio MUST be muxed from master.wav after render (HF flattens dynamics).
SAMPLE=1 -> render intro + #5 + outro pilot. HTML_ONLY=1 -> skip audio rebuild.
"""
import contextlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
RAW = ROOT / "raw"
CS = ROOT / "clips_seg"
CS.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT.parents[1]))  # repo root -> import tools
from tools.video import showcase_align  # noqa: E402

SAMPLE = os.environ.get("SAMPLE") == "1"
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

# intro/outro music bed = 打了一把钥匙给你 (#1, the climax) — soft instr for intro, chorus for outro
INTRO_BED_AUD = "p1_key"
INTRO_BED_SEEK = 4.5
OUTRO_BED_AUD = "p1_key"
OUTRO_BED_SEEK = 22.0


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


# reveal order 5 -> 1. ch_off = chorus onset in vert-clip local time (== showcase full-music start);
# show = showcase seconds. Both derived from vocal_analysis + frame checks (see SOURCES.md).
ITEMS = [
    {
        "key": "p5_nanhai", "no": "05",
        "name": "《我曾爱过一个男孩》", "plain": "我曾爱过一个男孩", "meta": "我等你 · 2000",
        "show": 30.67, "ch_off": 56.0, "mgain": 0.92,  # extended: finish the 10.8s chorus phrase (was cut mid-phrase @src173)
        "tag": "回头才发现，他一直都在",
        "note": "把怀旧唱得不矫情，只剩淡淡的心动",
    },
    {
        "key": "p4_gelou", "no": "04",
        "name": "《阁楼》", "plain": "阁楼", "meta": "到处乱走 · 1996",
        # DECOUPLED: 单身日誌 Live 源音轨人声被埋/无前置人声(用户两次听出"完全没人声")
        # -> 用 1996 录音室版(干净人声)做音乐，Live 画面(她特写)做视觉。慢歌口型微差可接受。
        "show": 25.7, "ch_off": 24.0, "mgain": 1.07, "aud_src": "p4_studio", "aud_ch": 180.23,
        "tag": "像推开一间很久没进的房间",
        "note": "藏着她早期作品里的电影感和空间感",
    },
    {
        "key": "p3_touming", "no": "03",
        "name": "《透明》", "plain": "透明", "meta": "很爱很爱你 · 1998",
        "show": 18.9, "ch_off": 24.31, "mgain": 0.89,  # was -14.1dB (hottest) -> trim to ~-15.1
        "tag": "把敏感和无力，唱得很轻",
        "note": "像真的经历过，才有的那种语气",
    },
    {
        "key": "p2_juzishu", "no": "02",
        "name": "《点亮橘子树》", "plain": "点亮橘子树", "meta": "年华 · 2001",
        "show": 27.67, "ch_off": 20.53, "mgain": 1.0,
        "tag": "橘子树、光，还有回忆",
        "note": "童话感，和旧时光的温度",
    },
    {
        "key": "p1_key", "no": "01",
        "name": "《打了一把钥匙给你》", "plain": "打了一把钥匙给你", "meta": "雨季 · 1995",
        "show": 26.0, "ch_off": 22.0, "mgain": 1.15,  # climax was -16.4dB (quietest) -> lift to ~-15.2
        "tag": "把一段关系，慢慢说给你听",
        "note": "刘若英最迷人的，是她的叙事感",
    },
]

items = [ITEMS[0]] if SAMPLE else ITEMS

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
    full_start_local = q(full_start - t)
    mseek = q(max(0, item["ch_off"] - full_start_local))  # video slice start
    aud_src = item.get("aud_src", item["key"])             # decoupled music source (default = coupled)
    aud_ch = item.get("aud_ch", item["ch_off"])
    aud_mseek = q(max(0, aud_ch - full_start_local))       # music slice start
    block = {
        **item,
        "clip": f"vert_{item['key']}", "aud_src": aud_src,
        "start": q(t), "end": end,
        "narr_start": narr_start, "narr_end": narr_end,
        "full_start": full_start, "full_start_local": full_start_local,
        "mseek": mseek, "aud_mseek": aud_mseek, "seg_dur": q(end - t),
    }
    blocks.append(block)
    t = end

# ---- 🔒 showcase alignment gate (FAIL -> no master) ----
# Only coupled songs (footage audio == music) go through the vert-clip vocal gate.
# Decoupled songs (aud_src != key, e.g. #4 studio audio under Live footage) are aligned
# against their own clean source vocals (manually verified) and skip this gate.
gate_blocks = [b for b in blocks if b["aud_src"] == b["key"]]
showcase_align.gate(gate_blocks, ROOT / "probe" / "vocal_analysis.json",
                    consts=dict(POST=POST, DIG=DIG, LEAD=LEAD),
                    plan_path=ROOT / "build" / "showcase_plan.json")

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

if not HTML_ONLY:
    # ---- intro: footage video-only slice + bed (#1 soft instr) + voice ----
    run([
        "ffmpeg", "-v", "error", "-i", str(C / "vert_intro.mp4"), "-t", str(intro_end),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / "intro.mp4"), "-y",
    ])
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(INTRO_BED_SEEK), "-i", str(RAW / f"{INTRO_BED_AUD}_aud.wav"),
        "-i", str(A / "intro.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.12,afade=t=in:st=0:d=0.7,afade=t=out:st={q(intro_end-0.8)}:d=0.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ])
segments.append("seg_intro.wav")

for block in blocks:
    seg = CS / f"{block['key']}.mp4"
    if not HTML_ONLY:
        # COUPLED — VIDEO: slice footage from mseek (so chorus lands at showcase start), video-only
        run([
            "ffmpeg", "-v", "error", "-ss", str(block["mseek"]), "-i", str(C / f"vert_{block['key']}.mp4"),
            "-t", str(block["seg_dur"]),
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
            str(seg), "-y",
        ])
        # COUPLED — MUSIC: same source's audio sliced from same mseek -> lip-sync preserved
        narr_end_local = q(LEAD + block["voice_dur"])
        env = envelope(narr_end_local, block["full_start_local"])
        gain = block.get("mgain", 1.0)
        out = f"seg_{block['key']}.wav"
        run([
            "ffmpeg", "-v", "error",
            "-ss", str(block["aud_mseek"]), "-i", str(RAW / f"{block['aud_src']}_aud.wav"),
            "-i", str(A / f"{block['key']}.wav"),
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{block['seg_dur']},volume={gain},volume='{env}':eval=frame[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=level=disabled:limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ])
    segments.append(f"seg_{block['key']}.wav")

outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
if not HTML_ONLY:
    run([
        "ffmpeg", "-v", "error", "-i", str(C / "vert_outro.mp4"), "-t", str(outro_dur),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        str(CS / "outro.mp4"), "-y",
    ])
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(OUTRO_BED_SEEK), "-i", str(RAW / f"{OUTRO_BED_AUD}_aud.wav"),
        "-i", str(A / "outro.wav"),
        "-i", str(A / "outro_cta.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.18,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ])
segments.append("seg_outro.wav")

# ---- concat ALL footage segments -> ONE footage_track.mp4 (HF multi-<video> hang fix; 1 video element only) ----
video_segs = ["intro.mp4"] + [f"{b['key']}.mp4" for b in blocks] + ["outro.mp4"]
if not HTML_ONLY:
    (ROOT / "vseglist.txt").write_text(
        "".join(f"file 'clips_seg/{name}'\n" for name in video_segs), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "vseglist.txt",
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", "-movflags", "+faststart", str(ROOT / "footage_track.mp4"), "-y",
    ])
    print("footage_track dur:", subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(ROOT / "footage_track.mp4")], capture_output=True, text=True).stdout.strip())

if not HTML_ONLY:
    (ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
        "-af", f"volume={MASTER_GAIN},alimiter=level=disabled:limit=0.97",
        "-ac", "2", "-ar", "48000", "master.wav", "-y",
    ])
    print("master dur:", dur(ROOT / "master.wav"), "planned:", total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="{src}" muted playsinline></video>'
    )


# Single footage track (one <video> element) — avoids HF multi-video frame-0 protocolTimeout hang.
videos = [video_tag(0, 0, total, "footage_track.mp4")]

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
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.54,scaleY:.04}},{{opacity:0,scaleY:1,duration:.78,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "我曾爱过一个男孩"),
        ("04", "阁楼"),
        ("03", "透明"),
        ("02", "点亮橘子树"),
        ("01", "打了一把钥匙给你"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0c0a0b;
  font-family:"PingFang SC",system-ui,sans-serif;color:#f3ece6;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0c0a0b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(12,10,11,.90),rgba(12,10,11,.06) 32%,rgba(12,10,11,.20) 56%,rgba(8,6,7,.95))}
#glow{position:absolute;inset:-260px;z-index:1;opacity:.40;background:radial-gradient(42% 26% at 16% 18%,rgba(230,170,135,.42),rgba(230,170,135,0) 65%),radial-gradient(48% 30% at 84% 80%,rgba(196,128,108,.28),rgba(196,128,108,0) 68%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.06;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(243,236,230,.13) 0 1px,rgba(243,236,230,0) 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(232,180,150,0),rgba(232,180,150,.52),rgba(196,128,108,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:128px 76px 120px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(12,10,11,.82),rgba(12,10,11,.12) 30%,rgba(12,10,11,.22) 56%,rgba(8,6,7,.93))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#e8b39c;letter-spacing:.12em}
.eyebrow:before{content:"";width:58px;height:4px;background:#e8b39c;border-radius:99px;box-shadow:0 0 18px rgba(232,179,156,.60)}
#cover h1{margin-top:30px;font-family:"Songti SC",serif;font-size:108px;line-height:1.1;font-weight:900;max-width:944px;text-shadow:0 6px 42px rgba(0,0,0,.70)}
#cover h1 b{color:#f0c7a3;font-weight:900}
#cover .sub{margin-top:30px;font-size:36px;line-height:1.5;color:#e6dcd2;font-weight:600;max-width:912px;text-shadow:0 2px 16px rgba(0,0,0,.55)}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:932px}
.chips span{border:1.5px solid rgba(232,179,156,.50);color:#f1e2d6;background:rgba(12,10,11,.55);font-size:27px;font-weight:800;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:64px;right:64px;bottom:172px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(12,10,11,.91),rgba(40,26,22,.56));border-left:8px solid #c4806c;border-radius:6px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.36)}
.fullLabel .rank{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e8b39c;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#bfa99c;letter-spacing:.06em}
.fullLabel h2{font-family:"Songti SC",serif;margin-top:12px;font-size:74px;line-height:1.14;font-weight:900;color:#f3ece6}
.fullLabel .tag{margin-top:19px;font-size:39px;line-height:1.28;font-weight:900;color:#f0c7a3}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#e6dcd2}
.fullLabel.topRank{border-left-color:#e8c977;background:linear-gradient(135deg,rgba(20,15,8,.93),rgba(12,10,11,.60))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f0d488}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(12,10,11,.70);border:1.5px solid rgba(232,179,156,.52);border-radius:8px}
.miniLabel span{font-family:"JetBrains Mono",monospace;font-size:44px;font-weight:900;color:#f3ece6;background:#0c0a0b;border:1px solid rgba(232,179,156,.50);border-radius:6px;padding:2px 8px;line-height:1.1}
.miniLabel strong{font-family:"Songti SC",serif;font-size:36px;font-weight:900;max-width:790px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(232,201,119,.76)}
.miniLabel.topRank span{border-color:rgba(232,201,119,.70)}
#outro{position:absolute;z-index:5;inset:0;padding:114px 72px 150px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(12,10,11,.40),rgba(8,6,7,.90))}
#outro .small{font-family:"JetBrains Mono",monospace;font-size:31px;font-weight:900;color:#e8b39c;letter-spacing:.14em}
#outro h2{font-family:"Songti SC",serif;margin-top:20px;font-size:54px;line-height:1.3;font-weight:900;max-width:932px}
#outro ol{margin-top:36px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 20px;background:rgba(12,10,11,.64);border:1px solid rgba(243,236,230,.14);border-radius:8px}
#outro li span{font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:900;color:#f3ece6;background:#0c0a0b;border:1px solid rgba(232,179,156,.45);border-radius:6px;padding:4px 8px;line-height:1.1;min-width:58px;text-align:center}
#outro li:last-child{background:rgba(232,201,119,.14);border-color:rgba(232,201,119,.45)}
#outro li:last-child span{border-color:rgba(232,201,119,.65)}
#outro li strong{font-family:"Songti SC",serif;font-size:33px;font-weight:900;text-align:right}
#outro .close{margin-top:30px;font-size:30px;line-height:1.5;color:#e6dcd2;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:90px;text-align:center;padding:20px;background:rgba(12,10,11,.72);border:1.5px solid rgba(232,201,119,.42);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#f0d488;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#e8b39c;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="glow" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<img id="coverhero" class="clip" data-start="0" data-duration="{q(intro_end-.08)}" data-track-index="11" '
    f'src="cover_hero.png" style="position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:4" />'
)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 不只是《后来》</div><h1>刘若英<br><b>最被低估</b>的5首歌</h1>'
    '<p class="sub">她最动人的，从来不是技巧，而是那种像在跟你讲心事的语气。这五首，藏着被大热歌盖过的另一个刘若英。</p></div>'
    '<div class="chips"><span>叙事感</span><span>文艺遗珠</span><span>旧时光</span><span>温柔不甜腻</span><span>越听越深</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>刘若英最珍贵的，从来不是高音和技巧，而是那种像在跟你讲心事的语气。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">这些被大热歌盖过的遗珠，刚好补齐了她最被低估的另一面。</p></section>'
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
tl.to("#coverhero",{{opacity:0,duration:.42,ease:"power1.in"}},{q(intro_end-.5)});
tl.set("#coverhero",{{opacity:0}},{q(intro_end)});
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
    "id": "main", "name": "liuruoying-underrated-top5", "sample": SAMPLE,
    "total": total, "intro_end": intro_end, "outro_start": outro_start,
    "blocks": [
        {"no": b["no"], "plain": b["plain"], "start": b["start"], "narr_start": b["narr_start"],
         "narr_end": b["narr_end"], "full_start": b["full_start"], "end": b["end"],
         "mseek": b["mseek"], "ch_off": b["ch_off"], "show": b["show"]}
        for b in blocks
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start, "SAMPLE:", SAMPLE)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], "mseek", b["mseek"]) for b in blocks])
