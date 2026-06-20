#!/usr/bin/env python3
"""No-server fallback renderer for the 金海心 countdown.

HyperFrames render needs a localhost file server, which can be blocked by the
managed sandbox. This script keeps the same timeline and master.wav, but renders
the visual layer with FFmpeg + ASS subtitles only.
"""
from __future__ import annotations

import contextlib
import json
import subprocess
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
BUILD = ROOT / "build"
RENDERS = ROOT / "renders"

SHOW = 31.0
LEAD = 0.35
DIG = 1.5
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
CTA_GAP = 1.0
OUTRO_TAIL = 1.8
INTRO_CLIP = "vert_p2_sleep"
OUTRO_CLIP = "vert_p1_right"


def wav_dur(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value: float) -> float:
    return round(float(value), 3)


def ass_time(t: float) -> str:
    total_cs = int(round(t * 100))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ev(layer: int, start: float, end: float, style: str, text: str) -> str:
    return (
        f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},"
        f"{style},,0,0,0,,{text}"
    )


items = [
    {
        "key": "p5_laibuji", "clip": "vert_p5_laibuji", "no": "05",
        "name": "《来不及》", "plain": "来不及",
        "tag": "慢半拍才意识到失去",
        "note": "被《那么骄傲》专辑光芒盖住的耐听遗珠",
    },
    {
        "key": "p4_bitian", "clip": "vert_p4_bitian", "no": "04",
        "name": "《比天空还远的季节》", "plain": "比天空还远的季节",
        "tag": "安静、内向、远远的孤独",
        "note": "《独立日》里更适合夜里重听的一首",
    },
    {
        "key": "p3_duian", "clip": "vert_p3_duian", "no": "03",
        "name": "《对岸》", "plain": "对岸",
        "tag": "看得见，却很难抵达",
        "note": "透明声线唱有距离的情绪，后劲更深",
    },
    {
        "key": "p2_sleep", "clip": "vert_p2_sleep", "no": "02",
        "name": "《睡不着的海》", "plain": "睡不着的海",
        "tag": "海、夜与不安",
        "note": "早期被标题曲压住的氛围宝藏",
    },
    {
        "key": "p1_right", "clip": "vert_p1_right", "no": "01",
        "name": "《右手戒指》", "plain": "右手戒指",
        "tag": "明亮的自我解放",
        "note": "《独立日》第二波概念主打，却很少被路人提起",
    },
]

for item in items:
    item["voice_dur"] = wav_dur(A / f"{item['key']}.wav")

d_intro = wav_dur(A / "intro.wav")
d_outro = wav_dur(A / "outro.wav")
d_cta = wav_dur(A / "cta.wav")
intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)

t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + SHOW)
    blocks.append({**item, "start": q(t), "full_start": full_start, "end": end})
    t = end

outro_start = q(t)
cta_start_local = q(LEAD + d_outro + CTA_GAP)
cta_abs = q(outro_start + cta_start_local)
total = q(outro_start + cta_start_local + d_cta + OUTRO_TAIL)

ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CoverTitle,STHeiti,94,&H00F4EFE4,&H000000FF,&H9A08090B,&H0008090B,1,0,0,0,100,100,0,0,1,2,3,7,70,70,120,1
Style: CoverSub,STHeiti,38,&H00D8E0DC,&H000000FF,&HAA08090B,&H0008090B,1,0,0,0,100,100,0,0,1,1,2,7,72,72,410,1
Style: CoverChip,STHeiti,30,&H00EFD493,&H000000FF,&H0008090B,&HBC1A1E22,1,0,0,0,100,100,0,0,3,2,0,2,64,64,138,1
Style: FullRank,STHeiti,32,&H005FAFD8,&H000000FF,&H0008090B,&HCA08090B,1,0,0,0,100,100,0,0,3,4,0,1,66,66,390,1
Style: FullTitle,STHeiti,74,&H00F4EFE4,&H000000FF,&H0008090B,&HCA08090B,1,0,0,0,100,100,0,0,3,5,0,1,66,66,305,1
Style: FullTag,STHeiti,42,&H0093D4EF,&H000000FF,&H0008090B,&HCA08090B,1,0,0,0,100,100,0,0,3,4,0,1,66,66,242,1
Style: FullNote,STHeiti,30,&H00D1D4C9,&H000000FF,&H0008090B,&HCA08090B,0,0,0,0,100,100,0,0,3,4,0,1,66,66,190,1
Style: Mini,STHeiti,36,&H00F4EFE4,&H000000FF,&H0008090B,&HBA08090B,1,0,0,0,100,100,0,0,3,4,0,7,56,56,92,1
Style: OutroTitle,STHeiti,56,&H00F4EFE4,&H000000FF,&H0008090B,&HBA08090B,1,0,0,0,100,100,0,0,3,4,0,7,70,70,210,1
Style: OutroRow,STHeiti,34,&H00F4EFE4,&H000000FF,&H0008090B,&HBA08090B,1,0,0,0,100,100,0,0,3,4,0,7,95,95,430,1
Style: CTA,STHeiti,45,&H00F4EFE4,&H000000FF,&H0008090B,&HCC151B1F,1,0,0,0,100,100,0,0,3,4,0,2,58,58,126,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

events = [
    ev(1, 0.35, intro_end - 0.35, "CoverTitle", r"{\fad(280,420)}金海心最被低估的\N5首歌"),
    ev(1, 2.2, intro_end - 0.45, "CoverSub", r"{\fad(260,380)}不先公布完整名单。\N从第五名开始，听那些被专辑光芒压住、\N却越听越有后劲的歌。"),
    ev(1, 3.4, intro_end - 0.45, "CoverChip", r"{\fad(260,380)}专辑遗珠    透明感声线    夜里重听    被低估的明亮"),
]

for b in blocks:
    fade = r"{\fad(180,260)}"
    color = r"{\c&H8894FF&}" if b["no"] == "01" else ""
    events.append(ev(2, b["start"] + 0.15, b["full_start"] - 0.2, "FullRank", f"{fade}{color}第 {b['no']} 名"))
    events.append(ev(2, b["start"] + 0.45, b["full_start"] - 0.2, "FullTitle", f"{fade}{color}{b['name']}"))
    events.append(ev(2, b["start"] + 0.9, b["full_start"] - 0.2, "FullTag", f"{fade}{b['tag']}"))
    events.append(ev(2, b["start"] + 1.2, b["full_start"] - 0.2, "FullNote", f"{fade}{b['note']}"))
    events.append(ev(2, b["full_start"] + 0.1, b["end"] - 0.3, "Mini", f"{fade}{b['no']}  {b['plain']}"))

events.extend([
    ev(2, outro_start + 0.2, total - 1.2, "OutroTitle", r"{\fad(240,420)}完整榜单\N这些歌不一定最大声，却最能听见金海心声音里的光。"),
    ev(2, outro_start + 2.0, total - 1.2, "OutroRow", r"{\fad(240,420)}01  右手戒指\N02  睡不着的海\N03  对岸\N04  比天空还远的季节\N05  来不及"),
    ev(3, cta_abs - 0.3, total - 0.35, "CTA", r"{\fad(220,520)}你最想为哪一首投票？\N点赞    收藏    关注"),
])

overlay_path = BUILD / "overlay.ass"
overlay_path.write_text(ass_header + "\n".join(events) + "\n", encoding="utf-8")

video_plan = [
    (C / f"{INTRO_CLIP}.mp4", intro_end),
    (C / "vert_p5_laibuji.mp4", q(blocks[0]["end"] - blocks[0]["start"])),
    (C / "vert_p4_bitian.mp4", q(blocks[1]["end"] - blocks[1]["start"])),
    (C / "vert_p3_duian.mp4", q(blocks[2]["end"] - blocks[2]["start"])),
    (C / "vert_p2_sleep.mp4", q(blocks[3]["end"] - blocks[3]["start"])),
    (C / "vert_p1_right.mp4", q(blocks[4]["end"] - blocks[4]["start"])),
    (C / f"{OUTRO_CLIP}.mp4", q(total - outro_start)),
]

cmd = ["ffmpeg", "-v", "error"]
for src, _duration in video_plan:
    cmd.extend(["-i", str(src)])
cmd.extend(["-i", str(ROOT / "master.wav")])

filters = []
for idx, (_src, duration) in enumerate(video_plan):
    filters.append(
        f"[{idx}:v]trim=0:{duration},setpts=PTS-STARTPTS,"
        f"scale=1080:1920,setsar=1[v{idx}]"
    )
concat_inputs = "".join(f"[v{idx}]" for idx in range(len(video_plan)))
filters.append(
    f"{concat_inputs}concat=n={len(video_plan)}:v=1:a=0,"
    f"format=yuv420p,ass=filename={overlay_path.relative_to(ROOT).as_posix()}[v]"
)

out = RENDERS / "jinhaixin-underrated-top5.mp4"
cmd.extend([
    "-filter_complex", ";".join(filters),
    "-map", "[v]",
    "-map", f"{len(video_plan)}:a",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-r", "30",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    str(out),
    "-y",
])

subprocess.run(cmd, cwd=ROOT, check=True)
(ROOT / "meta.json").write_text(
    json.dumps(
        {
            "id": "main",
            "name": "jinhaixin-underrated-top5",
            "duration": total,
            "renderer": "ffmpeg-fallback",
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(f"wrote {out.relative_to(ROOT)}")
print("duration:", total)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
