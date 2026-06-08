from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "outro_card.png"
W, H = 1080, 1920

FONT = Path("/Library/Fonts/Arial Unicode.ttf")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H), "#07100d")
    draw = ImageDraw.Draw(img)

    # Subtle vertical gradient so the static outro does not feel flat.
    for y in range(H):
        t = y / H
        r = int(7 + 8 * t)
        g = int(16 + 20 * (1 - t))
        b = int(13 + 15 * (1 - t))
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-260, 120, 520, 900), fill=(34, 113, 92, 46))
    gd.ellipse((600, 20, 1300, 720), fill=(154, 84, 120, 34))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    draw = ImageDraw.Draw(img)

    gold = "#d7bd78"
    pink = "#ff77b7"
    muted = "#b7c3b8"
    white = "#f8f7ef"

    draw.text((86, 310), "最终榜单", font=font(42), fill=gold)
    draw.text((86, 390), "那英最难的5首歌", font=font(82), fill=white)
    draw.line((86, 515, 994, 515), fill=(215, 189, 120, 110), width=2)

    rows = [
        ("01", "征服", pink),
        ("02", "默", gold),
        ("03", "白天不懂夜的黑", gold),
        ("04", "出卖", gold),
        ("05", "不管有多苦", gold),
    ]

    y = 610
    for rank, title, color in rows:
        draw.rounded_rectangle((86, y, 994, y + 116), radius=14, fill="#10201d", outline="#31483f", width=1)
        draw.text((126, y + 26), rank, font=font(48), fill=color)
        draw.text((285, y + 25), title, font=font(52), fill=white)
        y += 132

    draw.text((86, 1320), "从第五名一路推到第一名：", font=font(42), fill=muted)
    draw.text((86, 1390), "不管有多苦、出卖、白天不懂夜的黑、默、征服。", font=font(42), fill=white)
    draw.text((86, 1500), "难在力量、沙哑和亮度，同时稳住。", font=font(46), fill=white)

    img.convert("RGB").save(OUT, quality=95)
    print(OUT)


if __name__ == "__main__":
    main()
