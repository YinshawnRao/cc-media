#!/usr/bin/env python3
"""把 frames/timeline/<src>/*.jpg 拼成时间轴 grid，左到右每帧加时间码标签。"""
import sys, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TL = ROOT / "frames/timeline"

def grid(src):
    d = TL / src
    files = sorted(d.glob("t*.jpg"), key=lambda p: int(re.search(r"t(\d+)", p.name).group(1)))
    if not files:
        return
    imgs = [Image.open(f) for f in files]
    w, h = imgs[0].size
    cols = 7
    rows = (len(imgs) + cols - 1) // cols
    out = Image.new("RGB", (w*cols, h*rows), "black")
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for i, (f, im) in enumerate(zip(files, imgs)):
        r, c = i // cols, i % cols
        x, y = c*w, r*h
        out.paste(im, (x, y))
        t = re.search(r"t(\d+)", f.name).group(1)
        draw.rectangle([x+4, y+4, x+60, y+28], fill="black")
        draw.text((x+8, y+6), f"{t}s", fill="yellow", font=font)
    outp = TL / f"{src}_grid.jpg"
    out.save(outp, quality=85)
    print(f"{src} -> {outp} ({len(imgs)} frames)")

for src in ["douwei_heibao", "faye_budokan", "jingtong_singer2026"]:
    grid(src)
