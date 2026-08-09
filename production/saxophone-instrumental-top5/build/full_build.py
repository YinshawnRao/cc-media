#!/usr/bin/env python3
"""Build the complete 最顶级的5首萨克斯纯音乐 vertical ranking video.

The authored picture is flattened to one seek-safe footage track. HyperFrames
renders against silence; the pre-mixed master is muxed only after rendering.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
RAW = ROOT / "raw"
CLIPS = ROOT / "clips"
SEG = ROOT / "clips_seg"
PROBE = ROOT / "probe"
for directory in (CLIPS, SEG, PROBE, ROOT / "renders", ROOT / "qa", ROOT / "vendor"):
    directory.mkdir(parents=True, exist_ok=True)

HTML_ONLY = os.environ.get("HTML_ONLY") == "1"

LEAD = 0.35
POST = 0.25
DIG = 1.45
BED = 0.13
VOICE_GAIN = 2.25
INTRO_VOICE_START = 0.55
INTRO_GAP = 1.05
OUTRO_LEAD = 0.45
OUTRO_DIGEST = 1.20
OUTRO_TAIL = 2.80
MASTER_GAIN = 0.98

ITEMS = [
    {
        "key": "p5", "no": "05", "raw": "p5_mister_magic_yt.mp4",
        "title": "Mister Magic", "artist": "GROVER WASHINGTON JR.",
        "op": "LIVE · 1981", "era": "SOUL JAZZ",
        "tag": "让萨克斯放下深情，开始真正地摇摆。",
        "note": "厚实暖音色 × 松弛律动 × 真实现场",
        "ch_off": 748.7, "show_end": 872.0, "crop": "1440:1080:0:0",
        "mgain": 1.00,
        "visual_evidence": "p5_window_sheet.jpg + p5_tail_sheet.jpg",
        "end_evidence": "现场独奏结束前收口，避开 873 秒后演职员表",
    },
    {
        "key": "p4", "no": "04", "raw": "p4_forever_in_love_bili.mp4",
        "title": "Forever in Love", "artist": "KENNY G",
        "op": "OFFICIAL VIDEO · 1992", "era": "ROMANCE",
        "tag": "像一段没有歌词的告白，浪漫却始终克制。",
        "note": "钢琴和弦 × 柔和弦乐 × 高音萨克斯",
        "ch_off": 104.8, "show_end": 170.3, "crop": "640:480:0:0",
        "mgain": 1.00,
        "visual_evidence": "p4_window_alt_sheet.jpg",
        "end_evidence": "分析确认的安静乐句边界；避开后段不适合叙事画面",
    },
    {
        "key": "p3", "no": "03", "raw": "p3_lily_was_here_bili.mp4",
        "title": "Lily Was Here", "artist": "DAVID A. STEWART & CANDY DULFER",
        "op": "OFFICIAL VIDEO · 1989", "era": "NOIR",
        "tag": "城市夜色里，慵懒、性感，又带一点危险。",
        "note": "电吉他 × 中音萨克斯 × 黑色电影气质",
        "ch_off": 183.9, "show_end": 258.4, "crop": "768:576:0:0",
        "mgain": 1.00,
        "visual_evidence": "p3_window_sheet.jpg + p3_tail_sheet.jpg",
        "end_evidence": "乐曲自然衰减终点",
    },
    {
        "key": "p2", "no": "02", "raw": "p2_going_home_yt.mp4",
        "title": "Going Home", "artist": "KENNY G",
        "op": "OFFICIAL VIDEO · 1990", "era": "HOMECOMING",
        "tag": "把黄昏和归途，变成人人听得懂的声音。",
        "note": "舒缓和弦 × 归途意象 × 经典旋律",
        "ch_off": 294.0, "show_end": 382.0, "crop": "1440:1080:0:0",
        "mgain": 1.00,
        "visual_evidence": "p2_window_sheet.jpg + p2_tail_sheet.jpg",
        "end_evidence": "演奏结束后、黑场出现前收口",
    },
    {
        "key": "p1", "no": "01", "raw": "p1_songbird_bili.mp4",
        "title": "Songbird", "artist": "KENNY G",
        "op": "OFFICIAL VIDEO · 1986", "era": "STANDARD",
        "tag": "简单、温暖又孤独，直抵现代萨克斯的标准答案。",
        "note": "极简旋律 × 温暖音色 × 永恒辨识度",
        "ch_off": 145.6, "show_end": 242.0, "crop": "640:480:0:0",
        "mgain": 1.00,
        "visual_evidence": "p1_window_sheet.jpg + p1_tail_sheet.jpg",
        "end_evidence": "片尾淡黑前的自然收束",
    },
]


def q(value: float) -> float:
    return round(float(value), 3)


def wav_duration(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as stream:
        return q(stream.getnframes() / stream.getframerate())


def media_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    return q(float(result.stdout.strip()))


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def make_letterbox(source: Path, target: Path, seek: float, duration: float, crop: str) -> None:
    """Hybrid keyframe seek plus exact output-side seek for frame-accurate clips."""
    if target.exists() and target.stat().st_size > 1024:
        try:
            if abs(media_duration(target) - duration) <= 0.04:
                return
        except subprocess.CalledProcessError:
            pass
    fast_seek = max(0.0, q(seek - 5.0))
    exact_seek = q(seek - fast_seek)
    fc = (
        f"[0:v]crop={crop},split=2[fg0][bg0];"
        "[bg0]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,gblur=sigma=42,eq=brightness=-0.28:saturation=0.68[bg];"
        "[fg0]scale=1080:-2:flags=lanczos[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,setpts=PTS-STARTPTS,format=yuv420p[out]"
    )
    run([
        "ffmpeg", "-v", "error", "-ss", str(fast_seek), "-i", str(source), "-ss", str(exact_seek), "-t", str(q(duration)),
        "-filter_complex", fc, "-map", "[out]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "19", "-r", "30", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", str(target), "-y",
    ])


d_intro = wav_duration(AUDIO / "intro.wav")
d_outro = wav_duration(AUDIO / "outro.wav")
d_cta = wav_duration(AUDIO / "outro_cta.wav")
for item in ITEMS:
    item["voice_dur"] = wav_duration(AUDIO / f"{item['key']}.wav")
    item["show"] = q(float(item["show_end"]) - float(item["ch_off"]))

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks: list[dict[str, object]] = []
for item in ITEMS:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + float(item["voice_dur"]))
    full_start = q(narr_end + POST + DIG)
    end = q(full_start + float(item["show"]))
    full_local = q(full_start - t)
    mseek = q(float(item["ch_off"]) - full_local)
    blocks.append({
        **item, "start": q(t), "end": end, "narr_start": narr_start, "narr_end": narr_end,
        "full_start": full_start, "full_start_local": full_local, "mseek": mseek,
        "seg_dur": q(end - t),
    })
    t = end

outro_start = q(t)
outro_voice = q(outro_start + OUTRO_LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + OUTRO_DIGEST)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)
outro_dur = q(total - outro_start)

# Pure-instrumental authoring gate: bind acoustic analysis, manual visual review,
# a detected phrase attack, and at least 60 seconds of uninterrupted music.
analysis_path = PROBE / "instrumental_analysis.json"
analysis_raw = analysis_path.read_bytes()
analysis = json.loads(analysis_raw)
analysis_by_key = {item["key"]: item for item in analysis["items"]}
plan_items: list[dict[str, object]] = []
for block in blocks:
    source_duration = media_duration(RAW / str(block["raw"]))
    start = float(block["ch_off"])
    show_end = float(block["show_end"])
    attacks = [float(x["time"]) for x in analysis_by_key[str(block["key"])]["strong_attacks"]]
    nearest = min(attacks, key=lambda value: abs(value - start))
    evidence_files = [name.strip() for name in str(block["visual_evidence"]).split("+")]
    evidence_ok = all((PROBE / name).exists() for name in evidence_files)
    ok = (
        float(block["show"]) >= 60.0
        and float(block["mseek"]) >= 0.0
        and show_end <= source_duration
        and abs(nearest - start) <= 0.11
        and evidence_ok
    )
    if not ok:
        raise RuntimeError(f"instrumental plan gate failed: {block['key']}")
    plan_items.append({
        "key": block["key"], "rank": block["no"], "source": block["raw"], "status": "OK",
        "phrase_attack_src": nearest, "full_music_start_src": start, "music_end_src": show_end,
        "continuous_show_duration": block["show"], "source_duration": source_duration,
        "visual_evidence": block["visual_evidence"], "end_evidence": block["end_evidence"],
    })
instrumental_plan = {
    "kind": "instrumental_phrase_and_visual_evidence",
    "status": "OK",
    "analysis_sha256": hashlib.sha256(analysis_raw).hexdigest(),
    "minimum_continuous_music_seconds": 60,
    "items": plan_items,
}
(PROBE / "instrumental_plan.json").write_text(
    json.dumps(instrumental_plan, ensure_ascii=False, indent=2), encoding="utf-8"
)


def envelope(narr_end_local: float, full_start_local: float) -> str:
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments: list[str] = []
if not HTML_ONLY:
    # Cover and rank 05 are source-continuous in both picture and sound.
    cover_seek = q(float(blocks[0]["mseek"]) - intro_end)
    make_letterbox(RAW / str(blocks[0]["raw"]), CLIPS / "vert_intro.mp4", cover_seek, intro_end, str(blocks[0]["crop"]))
    for block in blocks:
        make_letterbox(
            RAW / str(block["raw"]), CLIPS / f"vert_{block['key']}.mp4",
            float(block["mseek"]), float(block["seg_dur"]), str(block["crop"]),
        )
    make_letterbox(RAW / "p1_songbird_bili.mp4", CLIPS / "vert_outro.mp4", 64.0, outro_dur, "640:480:0:0")

    run([
        "ffmpeg", "-v", "error", "-i", str(RAW / str(blocks[0]["raw"])), "-i", str(AUDIO / "intro.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]atrim=start={cover_seek}:end={q(cover_seek+intro_end)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
        f"loudnorm=I=-16:TP=-1.0:LRA=11,volume=0.12,afade=t=in:st=0:d=0.65,afade=t=out:st={q(intro_end-.65)}:d=0.65[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=level=disabled:limit=.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ])
    segments.append("seg_intro.wav")

    for block in blocks:
        narr_end_local = q(LEAD + float(block["voice_dur"]))
        env = envelope(narr_end_local, float(block["full_start_local"]))
        fade_start = q(float(block["seg_dur"]) - .55)
        output = f"seg_{block['key']}.wav"
        run([
            "ffmpeg", "-v", "error", "-i", str(RAW / str(block["raw"])), "-i", str(AUDIO / f"{block['key']}.wav"),
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]atrim=start={block['mseek']}:end={q(float(block['mseek'])+float(block['seg_dur']))},asetpts=PTS-STARTPTS,"
            f"aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,volume={block['mgain']},"
            f"volume='{env}':eval=frame,afade=t=out:st={fade_start}:d=0.55[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=level=disabled:limit=.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", output, "-y",
        ])
        segments.append(output)

    cta_local = q(cta_voice - outro_start)
    run([
        "ffmpeg", "-v", "error", "-i", str(RAW / "p1_songbird_bili.mp4"),
        "-i", str(AUDIO / "outro.wav"), "-i", str(AUDIO / "outro_cta.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(OUTRO_LEAD*1000)}|{int(OUTRO_LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]atrim=start=64:end={q(64+outro_dur)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
        f"loudnorm=I=-16:TP=-1.0:LRA=11,volume=.14,afade=t=in:st=0:d=0.7,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ])
    segments.append("seg_outro.wav")

    footage = ["clips/vert_intro.mp4"] + [f"clips/vert_{b['key']}.mp4" for b in blocks] + ["clips/vert_outro.mp4"]
    (ROOT / "footage_seglist.txt").write_text("".join(f"file '{name}'\n" for name in footage), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "footage_seglist.txt", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-sc_threshold", "0", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", str(SEG / "footage_track.mp4"), "-y",
    ])
    (ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
    run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
        "-af", f"volume={MASTER_GAIN},alimiter=level=disabled:limit=.97", "-ac", "2", "-ar", "48000", "master.wav", "-y",
    ])
    run([
        "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(total),
        "-c:a", "pcm_s16le", "render_silence.wav", "-y",
    ])
    if abs(wav_duration(ROOT / "master.wav") - total) > 0.05:
        raise RuntimeError("master duration drift")


rank_names = [(b["no"], b["title"], b["artist"]) for b in blocks]


def rail(active: str) -> str:
    return "".join(f'<span class="{"active" if no == active else ""}">{no}</span>' for no, _, _ in rank_names)


labels: list[str] = []
tweens: list[str] = []
transitions: list[str] = []
transition_tweens: list[str] = []
for index, block in enumerate(blocks):
    dossier = f"dossier{index}"
    mini = f"mini{index}"
    full_duration = q(float(block["full_start"]) - float(block["start"]))
    mini_duration = q(float(block["end"]) - float(block["full_start"]))
    top = " topRank" if block["no"] == "01" else ""
    labels.append(
        f'<section id="{dossier}" class="clip dossier{top}" data-start="{block["start"]}" data-duration="{full_duration}" data-track-index="{20+index}">'
        f'<div class="dHead"><span>RANK {block["no"]}</span><b>{block["op"]}</b><i>{block["era"]}</i></div>'
        f'<div class="rankGhost">{block["no"]}</div><div class="dBody"><div class="archive">BRASS MASTER / 夜色情绪档案</div>'
        f'<h2>{block["title"]}</h2><p class="artist">{block["artist"]}</p><div class="rule"></div>'
        f'<p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></div>'
        f'<div class="wave"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>'
        f'<div class="rankRail">{rail(str(block["no"]))}</div></section>'
    )
    labels.append(
        f'<section id="{mini}" class="clip mini{top}" data-start="{block["full_start"]}" data-duration="{mini_duration}" data-track-index="{30+index}">'
        f'<div>RANK {block["no"]} / FULL MUSIC</div><strong>{block["title"]}</strong><span>{block["artist"]}</span></section>'
    )
    s = float(block["start"])
    fs = float(block["full_start"])
    tweens.extend([
        f'tl.fromTo("#{dossier} .dHead",{{x:-42,opacity:0}},{{x:0,opacity:1,duration:.42,ease:"power3.out"}},{q(s+.18)});',
        f'tl.fromTo("#{dossier} .rankGhost",{{x:80,opacity:0}},{{x:0,opacity:.16,duration:.58,ease:"power4.out"}},{q(s+.28)});',
        f'tl.fromTo("#{dossier} .archive",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.38,ease:"power2.out"}},{q(s+.42)});',
        f'tl.fromTo("#{dossier} h2",{{y:56,opacity:0}},{{y:0,opacity:1,duration:.62,ease:"power4.out"}},{q(s+.52)});',
        f'tl.fromTo("#{dossier} .artist",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+.74)});',
        f'tl.fromTo("#{dossier} .rule",{{scaleX:0}},{{scaleX:1,duration:.52,ease:"power3.inOut"}},{q(s+.86)});',
        f'tl.fromTo("#{dossier} .tag",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power3.out"}},{q(s+1.00)});',
        f'tl.fromTo("#{dossier} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.42,ease:"power2.out"}},{q(s+1.20)});',
        f'tl.fromTo("#{mini}",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.38,ease:"power3.out"}},{q(fs+.08)});',
    ])

for index, point in enumerate([float(b["start"]) for b in blocks[1:]] + [outro_start]):
    code = f"gate{index}"
    transitions.append(
        f'<div id="{code}" class="clip gateCode" data-start="{q(point-.28)}" data-duration=".82" data-track-index="{50+index}">BRASS / CUT</div>'
    )
    transition_tweens.extend([
        f'tl.to("#footage",{{filter:"blur(16px)",scale:1.035,duration:.20,ease:"power2.in"}},{q(point-.20)});',
        f'tl.to("#gateLeft",{{x:0,duration:.22,ease:"power4.in"}},{q(point-.22)});',
        f'tl.to("#gateRight",{{x:0,duration:.22,ease:"power4.in"}},{q(point-.22)});',
        f'tl.fromTo("#{code}",{{scale:.84,opacity:0}},{{scale:1,opacity:1,duration:.16,ease:"power3.out"}},{q(point-.02)});',
        f'tl.to("#{code}",{{opacity:0,duration:.16,ease:"power2.in"}},{q(point+.15)});',
        f'tl.to("#gateLeft",{{x:-550,duration:.34,ease:"power4.out"}},{q(point+.10)});',
        f'tl.to("#gateRight",{{x:550,duration:.34,ease:"power4.out"}},{q(point+.10)});',
        f'tl.to("#footage",{{filter:"blur(0px)",scale:1,duration:.34,ease:"power2.out"}},{q(point+.10)});',
    ])

ranking_rows = "".join(
    f'<li><b>{no}</b><div><strong>{title}</strong><small>{artist}</small></div></li>' for no, title, artist in rank_names
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
@font-face{font-family:"PingFang SC";src:local("PingFang SC");font-weight:400 900}
@font-face{font-family:"Songti SC";src:local("Songti SC");font-weight:400 900}
@font-face{font-family:"Oswald";src:local("Oswald");font-weight:400 800}
@font-face{font-family:"JetBrains Mono";src:local("JetBrains Mono");font-weight:400 900}
html,body{width:1080px;height:1920px;overflow:hidden;background:#120d0e;color:#f5e8d3;font-family:"PingFang SC",sans-serif;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden}
#base{position:absolute;inset:0;background:#120d0e}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:fill;transform-origin:center;z-index:0}
#tint{position:absolute;inset:0;z-index:1;background:linear-gradient(180deg,rgba(18,13,14,.38),rgba(18,13,14,.08) 42%,rgba(18,13,14,.56))}
#frame{position:absolute;inset:38px;z-index:14;border:2px solid rgba(245,232,211,.34);pointer-events:none}
#frame:before,#frame:after{content:"";position:absolute;background:#c89b55}.clip{position:absolute}
#frame:before{left:-2px;top:80px;width:7px;height:172px}#frame:after{right:-2px;bottom:92px;width:7px;height:124px}
#folio{position:absolute;right:52px;top:64px;z-index:15;font:700 19px/1.2 "JetBrains Mono";letter-spacing:.18em;color:#dbc8aa;writing-mode:vertical-rl}
#cover{inset:0;z-index:5;padding:148px 72px 430px;display:flex;flex-direction:column;background:linear-gradient(180deg,rgba(18,13,14,.42),rgba(18,13,14,.10) 35%,rgba(18,13,14,.80))}
.coverTop{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid rgba(200,155,85,.68);padding-bottom:20px;font:700 22px "JetBrains Mono";letter-spacing:.13em}
.coverTop b{padding:8px 13px;background:#c89b55;color:#120d0e;font-size:25px}.coverMain{margin-top:auto;margin-bottom:92px}
.stamp{display:inline-block;border:3px solid #c89b55;padding:10px 16px;color:#e2bc7d;font:900 23px "JetBrains Mono";letter-spacing:.13em;transform:rotate(-2deg)}
#cover h1{margin-top:28px;font:900 118px/1.02 "Songti SC",serif;letter-spacing:-.055em;text-shadow:0 6px 0 #120d0e,0 16px 34px rgba(0,0,0,.78)}
#cover h1 em{display:inline-block;margin-top:12px;color:#f5e8d3;font:900 106px/.98 "Oswald",sans-serif;font-style:normal;letter-spacing:-.04em;-webkit-text-stroke:3px #c89b55;text-shadow:7px 7px 0 #7e5a29}
.dek{margin-top:30px;max-width:820px;border-left:8px solid #c89b55;padding-left:22px;font-size:35px;line-height:1.42;font-weight:800;text-shadow:0 4px 18px rgba(0,0,0,.8)}
.coverFoot{display:flex;justify-content:space-between;border-top:2px solid rgba(200,155,85,.55);padding-top:18px;font:700 20px "JetBrains Mono";letter-spacing:.09em;color:#dbc8aa}
.dossier{inset:0;z-index:5;padding:80px 68px 96px;background:rgba(18,13,14,.20)}
.dHead{display:grid;grid-template-columns:1fr auto auto;gap:18px;align-items:center;border-top:3px solid #f5e8d3;border-bottom:1px solid rgba(200,155,85,.62);padding:16px 0;font:700 20px "JetBrains Mono";letter-spacing:.08em}
.dHead span{font-size:28px;color:#e2bc7d}.dHead i{font-style:normal;color:#cbbba1}.rankGhost{position:absolute;right:34px;top:236px;font:900 340px/.8 "Oswald";color:#f5e8d3;-webkit-text-stroke:3px #f5e8d3;opacity:.16;letter-spacing:-.06em}
.dBody{position:absolute;left:68px;right:68px;bottom:170px;padding:32px 36px 36px;background:rgba(18,13,14,.91);border-left:8px solid #c89b55;border-top:1px solid rgba(200,155,85,.58)}
.archive{font:900 18px "JetBrains Mono";letter-spacing:.18em;color:#e2bc7d}.dBody h2{margin-top:14px;font:900 84px/1.02 "Oswald","Songti SC";overflow-wrap:anywhere;text-shadow:0 3px 20px #000}
.artist{margin-top:12px;font:800 25px/1.25 "JetBrains Mono";letter-spacing:.035em;color:#d1c2aa}.rule{height:5px;margin:24px 0 20px;background:#c89b55;transform-origin:left}
.tag{font-size:39px;line-height:1.34;font-weight:900}.note{margin-top:13px;font-size:25px;line-height:1.5;font-weight:700;color:#baa98f}
.wave{position:absolute;left:72px;top:312px;height:112px;display:flex;gap:11px;align-items:end;opacity:.72}.wave i{display:block;width:8px;background:#c89b55}.wave i:nth-child(1){height:38px}.wave i:nth-child(2){height:72px}.wave i:nth-child(3){height:52px}.wave i:nth-child(4){height:96px}.wave i:nth-child(5){height:65px}.wave i:nth-child(6){height:44px}.wave i:nth-child(7){height:84px}.wave i:nth-child(8){height:56px}.wave i:nth-child(9){height:102px}
.rankRail{position:absolute;right:54px;bottom:78px;display:flex;gap:9px;font:900 19px "JetBrains Mono"}.rankRail span{width:67px;border-top:4px solid #5a514b;padding-top:8px;color:#766d65;text-align:center}.rankRail span.active{border-color:#c89b55;color:#f5e8d3}
.topRank .dBody{border-left-color:#f0bf65}.topRank .dHead span,.topRank .archive{color:#f3c979}.topRank .rule{background:#f0bf65}
.mini{z-index:5;left:58px;top:74px;min-width:660px;max-width:930px;padding:17px 22px 19px 25px;background:rgba(18,13,14,.90);border-left:7px solid #c89b55;border-top:1px solid rgba(200,155,85,.62);display:grid;grid-template-columns:1fr auto;gap:6px 20px}
.mini div{grid-column:1/3;font:900 17px "JetBrains Mono";letter-spacing:.13em;color:#e2bc7d}.mini strong{font:900 39px/1.05 "Oswald","Songti SC";overflow-wrap:anywhere}.mini span{align-self:end;font:700 16px "JetBrains Mono";color:#bbaa90;text-align:right}.mini.topRank{border-left-color:#f0bf65}
#gate{position:absolute;inset:0;z-index:20;overflow:hidden;pointer-events:none}#gateLeft,#gateRight{position:absolute;top:0;width:540px;height:1920px;background:#120d0e}#gateLeft{left:0;border-right:5px solid #c89b55}#gateRight{right:0;border-left:5px solid #c89b55}
.gateCode{z-index:22;left:50%;top:50%;transform:translate(-50%,-50%);border:3px solid #c89b55;background:#120d0e;padding:16px 27px;font:900 28px "JetBrains Mono";letter-spacing:.16em;white-space:nowrap}
#outro{inset:0;z-index:5;padding:82px 68px 118px;background:rgba(18,13,14,.76)}.outHead{display:flex;justify-content:space-between;border-top:3px solid #f5e8d3;border-bottom:1px solid rgba(200,155,85,.62);padding:15px 0;font:700 20px "JetBrains Mono";letter-spacing:.12em}
#outro h2{margin-top:48px;font:900 70px/1.12 "Songti SC",serif}#outro h2 em{font-style:normal;color:#e2bc7d}#outro ol{list-style:none;margin-top:32px;display:grid;gap:11px}
#outro li{display:grid;grid-template-columns:72px 1fr;gap:18px;align-items:center;border-top:1px solid rgba(200,155,85,.46);padding:15px 14px;background:rgba(18,13,14,.70)}#outro li b{font:900 36px "Oswald";color:#e2bc7d}#outro li div{display:flex;justify-content:space-between;align-items:baseline;gap:18px}#outro li strong{font:900 31px "Oswald","Songti SC"}#outro li small{font:700 15px "JetBrains Mono";color:#a99a84;text-align:right}
.outClose{margin-top:26px;border-left:7px solid #c89b55;padding-left:20px;font-size:28px;line-height:1.5;font-weight:800;color:#dfcfb6}#cta{z-index:12;left:68px;right:68px;bottom:76px;padding:20px 24px;background:#120d0e;border:2px solid #f0bf65;text-align:center}.vote{font-size:37px;font-weight:900;color:#f0c878}.follow{margin-top:8px;font:900 21px "JetBrains Mono";letter-spacing:.16em}
"""

body = (
    f'<div id="base" class="clip" data-start="0" data-duration="{total}" data-track-index="0"></div>'
    f'<video id="footage" class="clip fv" data-start="0" data-duration="{total}" data-track-index="1" src="clips_seg/footage_track.mp4" muted playsinline></video>'
    f'<div id="tint" class="clip" data-start="0" data-duration="{total}" data-track-index="2"></div>'
    f'<div id="frame" class="clip" data-start="0" data-duration="{total}" data-track-index="14"></div>'
    f'<div id="folio" class="clip" data-start="0" data-duration="{total}" data-track-index="15">SAXOPHONE / MASTER ARCHIVE · 05→01</div>'
    f'<section id="cover" class="clip" data-start="0" data-duration="{intro_end}" data-track-index="5">'
    '<div class="coverTop"><span>MIDNIGHT BRASS / MASTER ARCHIVE</span><b>05→01</b></div>'
    '<div class="coverMain"><div class="stamp">TOP TIER / 夜色情绪</div><h1>最顶级的<br><em>5首萨克斯纯音乐</em></h1>'
    '<p class="dek">没有一句歌词，也能让空气先变成情绪。</p></div>'
    '<div class="coverFoot"><span>BRASS / AFTER DARK</span><span>MASTER RECORD · 2026</span></div></section>'
)
body += "".join(labels)
body += f'<div id="gate" class="clip" data-start="0" data-duration="{total}" data-track-index="18"><div id="gateLeft" data-layout-allow-overflow></div><div id="gateRight" data-layout-allow-overflow></div></div>'
body += "".join(transitions)
body += (
    f'<section id="outro" class="clip" data-start="{outro_start}" data-duration="{outro_dur}" data-track-index="6">'
    '<div class="outHead"><span>MIDNIGHT BRASS ARCHIVE</span><span>FINAL ORDER / 05→01</span></div>'
    '<h2>五段旋律，留下<br><em>五种没有歌词的情绪</em></h2>'
    f'<ol>{ranking_rows}</ol><p class="outClose">萨克斯一开口，每个人都会听见自己的故事。</p></section>'
    f'<section id="cta" class="clip" data-start="{q(cta_voice-.12)}" data-duration="{q(total-cta_voice+.12)}" data-track-index="16">'
    '<div class="vote">为你的第一名，评论区投票</div><div class="follow">点赞 · 收藏 · 关注</div></section>'
    f'<audio id="renderAudio" class="clip" data-start="0" data-duration="{total}" data-track-index="7" src="render_silence.wav" data-volume="1"></audio>'
)

js = f"""
tl.set("#cover, #cover .coverTop, #cover .stamp, #cover h1, #cover .dek, #cover .coverFoot",{{opacity:1,x:0,y:0}},0);
tl.set("#gateLeft",{{x:-550}},0);tl.set("#gateRight",{{x:550}},0);
tl.fromTo("#cover .stamp",{{rotation:-4,scale:.96}},{{rotation:-2,scale:1,duration:.34,ease:"power3.out"}},.12);
tl.fromTo("#cover h1",{{x:-7}},{{x:7,duration:4.4,ease:"sine.inOut",yoyo:true,repeat:1}},.18);
tl.fromTo("#cover .coverTop",{{scaleX:.98}},{{scaleX:1,duration:.45,ease:"power2.out"}},.08);
{chr(10).join(tweens)}
{chr(10).join(transition_tweens)}
tl.fromTo("#outro .outHead",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power3.out"}},{q(outro_start+.22)});
tl.fromTo("#outro h2",{{y:46,opacity:0}},{{y:0,opacity:1,duration:.62,ease:"power4.out"}},{q(outro_start+.48)});
tl.fromTo("#outro li",{{x:-38,opacity:0}},{{x:0,opacity:1,duration:.36,ease:"power3.out",stagger:.10}},{q(outro_start+.96)});
tl.fromTo("#outro .outClose",{{y:20,opacity:0}},{{y:0,opacity:1,duration:.42,ease:"power2.out"}},{q(outro_start+1.72)});
tl.fromTo("#cta .vote",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power3.out"}},{q(cta_voice)});
tl.fromTo("#cta .follow",{{y:15,opacity:0}},{{y:0,opacity:1,duration:.42,ease:"power2.out"}},{q(cta_voice+.28)});
tl.to("#root",{{opacity:0,duration:.50,ease:"power2.in"}},{q(total-.50)});
"""

html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080,height=1920">
<script src="vendor/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">{body}</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});{js}window.__timelines["main"]=tl;</script>
</body></html>"""
(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "meta.json").write_text(json.dumps({
    "id": "main", "name": "saxophone-instrumental-top5", "width": 1080, "height": 1920,
    "duration": total, "intro_end": intro_end, "outro_start": outro_start, "cta_start": cta_voice,
    "blocks": [{
        "key": b["key"], "rank": b["no"], "title": b["title"], "artist": b["artist"],
        "start": b["start"], "narr_start": b["narr_start"], "narr_end": b["narr_end"],
        "full_start": b["full_start"], "end": b["end"], "mseek": b["mseek"],
        "ch_off": b["ch_off"], "show_end": b["show_end"], "show": b["show"], "source": b["raw"],
    } for b in blocks],
}, ensure_ascii=False, indent=2), encoding="utf-8")

print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
for block in blocks:
    print(block["no"], block["title"], "timeline", block["start"], "->", block["end"],
          "source", block["mseek"], "->", q(float(block["mseek"]) + float(block["seg_dur"])),
          "full", block["ch_off"], "show", block["show"])
