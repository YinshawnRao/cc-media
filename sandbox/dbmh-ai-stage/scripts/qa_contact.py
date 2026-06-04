#!/usr/bin/env python3
"""QA contact sheet for rendered video frames."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "frames/qa"
OUT = ROOT / "frames/qa_contact.jpg"

files = sorted(SRC.glob("qa_*.jpg"), key=lambda p: int(re.search(r"qa_(\d+)", p.name).group(1)))
W, H = 270, 480
cols = 5
rows = (len(files) + cols - 1) // cols
img = Image.new("RGB", (W*cols, H*rows), "black")
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
except Exception:
    font = ImageFont.load_default()
for i, f in enumerate(files):
    r, c = i // cols, i % cols
    x, y = c*W, r*H
    img.paste(Image.open(f), (x, y))
    t = re.search(r"qa_(\d+)", f.name).group(1)
    draw.rectangle([x+4, y+4, x+90, y+44], fill="black")
    draw.text((x+10, y+8), f"{t}s", fill="yellow", font=font)
img.save(OUT, quality=85)
print(f"wrote {OUT}")
