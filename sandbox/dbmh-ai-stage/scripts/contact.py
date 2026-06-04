#!/usr/bin/env python3
"""把 frames/clips/*.jpg 拼成 contact sheet。每行 = 一个 clip 的 abc 三帧。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "frames/clips"
OUT = ROOT / "frames/clips_contact.jpg"

clips = ["dw_long", "fw_long", "jt_long", "dw_three", "fw_three", "jt_three", "jt_outro"]
W, H = 270, 480
img = Image.new("RGB", (W*3 + 200, H*len(clips)), "black")
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
except Exception:
    font = ImageFont.load_default()
for r, c in enumerate(clips):
    draw.text((10, r*H + 20), c, fill="yellow", font=font)
    for ci, suf in enumerate(["a", "b", "c"]):
        p = SRC / f"{c}_{suf}.jpg"
        if p.exists():
            im = Image.open(p).resize((W, H))
            img.paste(im, (200 + ci*W, r*H))
img.save(OUT, quality=80)
print(f"wrote {OUT}")
