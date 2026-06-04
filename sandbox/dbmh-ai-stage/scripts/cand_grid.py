#!/usr/bin/env python3
"""把候选帧拼成 grid，标时间码。"""
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "cover/cands"

def build(prefix, outname, cols=5):
    files = sorted(SRC.glob(f"{prefix}_*.jpg"),
                   key=lambda p: int(re.search(rf"{prefix}_(\d+)", p.name).group(1)))
    if not files: return
    imgs = [Image.open(f) for f in files]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    out = Image.new("RGB", (w*cols, h*rows), "black")
    draw = ImageDraw.Draw(out)
    try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
    except: font = ImageFont.load_default()
    for i, (f, im) in enumerate(zip(files, imgs)):
        r, c = i // cols, i % cols
        x, y = c*w, r*h
        out.paste(im, (x, y))
        t = re.search(rf"{prefix}_(\d+)", f.name).group(1)
        draw.rectangle([x+4, y+4, x+100, y+44], fill="black")
        draw.text((x+10, y+8), f"{t}s", fill="yellow", font=font)
    outp = ROOT / "frames" / outname
    out.save(outp, quality=85)
    print(outp)

build("fw", "fw_cands.jpg")
build("jt", "jt_cands.jpg")
