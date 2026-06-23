#!/usr/bin/env python3
"""No-server FFmpeg fallback render.

This is only for review when HyperFrames cannot bind a local file server in the
sandbox. It uses the same aligned clips and master.wav, then overlays static PNG
cards generated with Pillow.
"""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from project import ITEMS, RANKING_ROWS, ROOT

W, H = 1080, 1920
OUT = ROOT / "renders" / "eason-saddest-top5_fallback.mp4"
OVERLAYS = ROOT / "overlays"
FONT_HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


F_HEI_28 = font(FONT_HEI, 28)
F_HEI_31 = font(FONT_HEI, 31)
F_HEI_32 = font(FONT_HEI, 32)
F_HEI_36 = font(FONT_HEI, 36)
F_HEI_42 = font(FONT_HEI, 42)
F_HEI_48 = font(FONT_HEI, 48)
F_HEI_64 = font(FONT_HEI, 64)
F_SONG_40 = font(FONT_SONG, 40)
F_SONG_64 = font(FONT_SONG, 64)
F_SONG_90 = font(FONT_SONG, 90)
F_SONG_136 = font(FONT_SONG, 136)


def q(value):
    return round(float(value), 3)


def new_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def round_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, s, fnt, fill=(247, 243, 238, 255), anchor=None):
    draw.text(xy, s, font=fnt, fill=fill, anchor=anchor)


def wrap(draw, s, fnt, max_w):
    lines = []
    cur = ""
    for ch in s:
        trial = cur + ch
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def save(img, name):
    path = OVERLAYS / name
    img.save(path)
    return path


def gradient_scrim():
    img = new_layer()
    pix = img.load()
    for y in range(H):
        top = max(0, 1 - y / 650)
        bottom = max(0, (y - 1120) / 800)
        alpha = int(170 * max(top, bottom, 0.25))
        for x in range(W):
            pix[x, y] = (6, 6, 8, alpha)
    return save(img, "scrim.png")


def cover():
    img = new_layer()
    d = ImageDraw.Draw(img)
    text(d, (74, 148), "苦情不是撕裂，是忍住", F_HEI_31, (213, 178, 119, 255))
    text(d, (74, 255), "陈奕迅", F_SONG_136)
    text(d, (74, 400), "最苦的5首歌", F_SONG_136, (247, 243, 238, 255))
    text(d, (513, 400), "5", F_SONG_136, (232, 201, 135, 255))
    sub = "他最狠的情歌，常常不是唱崩溃，而是唱一个人终于承认：有些山，真的搬不走。"
    y = 585
    for line in wrap(d, sub, F_HEI_36, 850):
        text(d, (74, y), line, F_HEI_36, (222, 216, 206, 255))
        y += 56
    chips = ["爱而不得", "余生感", "关系空城", "友情走散", "人生苦味"]
    x, y = 74, 1628
    for chip in chips:
        tw = d.textbbox((0, 0), chip, font=F_HEI_28)[2]
        round_rect(d, (x, y, x + tw + 40, y + 52), 26, (9, 9, 11, 132), (213, 178, 119, 150), 2)
        text(d, (x + 20, y + 11), chip, F_HEI_28, (243, 223, 179, 255))
        x += tw + 56
    return save(img, "cover.png")


def full_label(item):
    img = new_layer()
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 62, 1260, 1018, 1715
    round_rect(d, (x0, y0, x1, y1), 8, (8, 8, 11, 220))
    d.rectangle((x0, y0, x0 + 7, y1), fill=(241, 198, 92, 255) if item["no"] == "01" else (213, 178, 119, 255))
    acc = (255, 212, 106, 255) if item["no"] == "01" else (213, 178, 119, 255)
    text(d, (100, y0 + 36), f"第 {item['no']} 名", F_HEI_32, acc)
    text(d, (270, y0 + 39), item["year"], F_HEI_28, (167, 157, 143, 255))
    text(d, (100, y0 + 92), item["name"], F_SONG_90)
    text(d, (100, y0 + 210), item["tag"], F_HEI_42, (240, 217, 156, 255))
    yy = y0 + 282
    for line in wrap(d, item["note"], F_HEI_32, 820):
        text(d, (100, yy), line, F_HEI_32, (214, 208, 199, 255))
        yy += 46
    return save(img, f"full_{item['key']}.png")


def mini_label(item):
    img = new_layer()
    d = ImageDraw.Draw(img)
    x0, y0 = 54, 92
    label = item["plain"]
    tw = d.textbbox((0, 0), label, font=F_SONG_40)[2]
    round_rect(d, (x0, y0, x0 + tw + 120, y0 + 70), 35, (8, 8, 11, 170), (213, 178, 119, 155), 2)
    text(d, (x0 + 20, y0 + 11), item["no"], F_HEI_42, (213, 178, 119, 255))
    text(d, (x0 + 88, y0 + 14), label, F_SONG_40)
    return save(img, f"mini_{item['key']}.png")


def outro():
    img = new_layer()
    d = ImageDraw.Draw(img)
    text(d, (72, 560), "最 苦 榜 单", F_HEI_32, (213, 178, 119, 255))
    text(d, (72, 625), "陈奕迅最苦的，往往不是让你哭出来，", F_SONG_64)
    text(d, (72, 705), "是多年后突然懂了自己为什么放不下。", F_SONG_64)
    y = 850
    for n, name in RANKING_ROWS:
        round_rect(d, (72, y, 1008, y + 74), 8, (8, 8, 11, 170), (255, 255, 255, 35), 1)
        text(d, (100, y + 17), n, F_HEI_36, (255, 212, 106, 255) if n == "01" else (213, 178, 119, 255))
        text(d, (850, y + 13), name, F_SONG_40, anchor="ra")
        y += 92
    return save(img, "outro.png")


def cta():
    img = new_layer()
    d = ImageDraw.Draw(img)
    round_rect(d, (60, 1508, 1020, 1738), 14, (8, 8, 11, 225), (213, 178, 119, 170), 2)
    text(d, (540, 1562), "你最想为哪一首投票？", F_HEI_48, anchor="ma")
    text(d, (540, 1650), "点赞    收藏    关注", F_HEI_36, (243, 223, 179, 255), anchor="ma")
    return save(img, "cta.png")


def main():
    OVERLAYS.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
    overlay_specs = []
    overlay_specs.append((gradient_scrim(), 0, timeline["total"]))
    overlay_specs.append((cover(), 0, timeline["intro_end"] - 0.6))
    item_by_key = {item["key"]: item for item in ITEMS}
    for block in timeline["blocks"]:
        item = item_by_key[block["key"]]
        overlay_specs.append((full_label(item), block["start"], block["full_start"] - 0.45))
        overlay_specs.append((mini_label(item), block["full_start"] + 0.12, block["end"] - 0.4))
    d_outro = 15.72
    cta_abs = q(timeline["outro_start"] + 0.35 + d_outro + 1.0)
    overlay_specs.append((outro(), timeline["outro_start"], cta_abs - 0.45))
    overlay_specs.append((cta(), cta_abs - 0.3, timeline["total"] - 1.3))

    clip_specs = [
        ("clips/vert_cover.mp4", timeline["intro_end"]),
    ]
    for block in timeline["blocks"]:
        clip_specs.append((f"clips/vert_{block['key']}.mp4", q(block["end"] - block["start"])))
    clip_specs.append(("clips/vert_fushi.mp4", q(timeline["total"] - timeline["outro_start"])))

    args = ["ffmpeg", "-v", "error"]
    for path, _ in clip_specs:
        args += ["-i", path]
    for path, _, _ in overlay_specs:
        args += ["-loop", "1", "-i", str(path)]
    audio_idx = len(clip_specs) + len(overlay_specs)
    args += ["-i", "master.wav"]

    parts = []
    for idx, (_, duration) in enumerate(clip_specs):
        parts.append(f"[{idx}:v]trim=duration={duration},setpts=PTS-STARTPTS,setsar=1[v{idx}]")
    concat_inputs = "".join(f"[v{i}]" for i in range(len(clip_specs)))
    parts.append(f"{concat_inputs}concat=n={len(clip_specs)}:v=1:a=0[base]")
    cur = "base"
    for idx, (_, start, end) in enumerate(overlay_specs):
        image_idx = len(clip_specs) + idx
        out = f"ov{idx}"
        parts.append(f"[{cur}][{image_idx}:v]overlay=0:0:enable='between(t,{q(start)},{q(end)})'[{out}]")
        cur = out
    filter_complex = ";".join(parts)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    args += [
        "-filter_complex", filter_complex,
        "-map", f"[{cur}]",
        "-map", f"{audio_idx}:a",
        "-shortest",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(OUT),
        "-y",
    ]
    subprocess.run(args, cwd=ROOT, check=True)
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
