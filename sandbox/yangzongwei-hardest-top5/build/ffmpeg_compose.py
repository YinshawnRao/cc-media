#!/usr/bin/env python3
"""Offline FFmpeg compositor for 杨宗纬最难的5首歌.

HyperFrames source remains index.html; this fallback produces the deliverable
when the local browser/file-server render path is unavailable in the sandbox.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "clips"
O = ROOT / "overlays"
R = ROOT / "renders"
S = R / "ff_segments"
W, H = 1080, 1920

FONT_SANS = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
FONT_SERIF = Path("/System/Library/Fonts/Supplemental/Songti.ttc")
if not FONT_SANS.exists():
    FONT_SANS = Path("/System/Library/Fonts/STHeiti Medium.ttc")
if not FONT_SERIF.exists():
    FONT_SERIF = FONT_SANS

ITEMS = [
    {"key": "p5_yueguoshanqiu", "clip": "vert_yueguoshanqiu", "no": "05", "name": "《越过山丘》", "plain": "越过山丘", "tag": "难在把时间唱出重量", "note": "阅历感、沧桑感、自我回望"},
    {"key": "p4_liangliang", "clip": "vert_liangliang", "no": "04", "name": "《凉凉》", "plain": "凉凉", "tag": "合唱分寸比独唱爆发更难", "note": "厚度、收束、仙侠宿命感"},
    {"key": "p3_yicijiuhao", "clip": "vert_yicijiuhao", "no": "03", "name": "《一次就好》", "plain": "一次就好", "tag": "温柔长线最怕气息松", "note": "长旋律、稳定支撑、克制煽情"},
    {"key": "p2_qishidoumeiyou", "clip": "vert_qishidoumeiyou", "no": "02", "name": "《其实都没有》", "plain": "其实都没有", "tag": "空荡感本身要有重量", "note": "轻、稳、冷，再慢慢推开"},
    {"key": "p1_yangcong", "clip": "vert_yangcong", "no": "01", "name": "《洋葱》", "plain": "洋葱", "tag": "连续递进才是真正难点", "note": "气息、声压、情绪一层一层推高"},
]


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def fnt(path, size):
    return ImageFont.truetype(str(path), size)


def sans(size):
    return fnt(FONT_SANS, size)


def serif(size):
    return fnt(FONT_SERIF, size)


def text_w(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap(draw, text, font, max_width):
    lines, cur = [], ""
    for ch in text:
        trial = cur + ch
        if cur and text_w(draw, trial, font) > max_width:
            lines.append(cur)
            cur = ch.lstrip()
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, xy, lines, font, fill, gap=10, stroke=0):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 120))
        box = draw.textbbox((x, y), line, font=font, stroke_width=stroke)
        y = box[3] + gap
    return y


def scrim(draw, strong=False):
    for y in range(H):
        top = int((210 if strong else 160) * max(0, 1 - y / 720))
        bottom = int((220 if strong else 180) * max(0, (y - 1040) / 880))
        mid = 42 if strong else 26
        a = min(235, max(top, bottom, mid))
        draw.line((0, y, W, y), fill=(5, 6, 10, a))


def save(name, painter):
    O.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    painter(draw)
    path = O / f"{name}.png"
    img.save(path)
    return path


def intro_overlay():
    def painter(draw):
        scrim(draw, True)
        draw.text((590, 1468), "ASKA\nYANG", font=serif(142), fill=(248, 244, 237, 28), align="right")
        draw.rounded_rectangle((72, 148, 405, 204), radius=8, fill=(7, 8, 13, 150), outline=(201, 155, 85, 150), width=2)
        draw.rectangle((94, 174, 146, 178), fill=(201, 155, 85, 255))
        draw.text((164, 155), "声线难度盘点", font=sans(30), fill=(201, 155, 85, 255))
        draw.text((70, 268), "杨宗纬", font=serif(116), fill=(248, 244, 237, 255), stroke_width=2, stroke_fill=(0, 0, 0, 120))
        draw.text((70, 405), "最难的5首歌", font=serif(124), fill=(248, 244, 237, 255), stroke_width=2, stroke_fill=(0, 0, 0, 120))
        lines = wrap(draw, "不只看高音。真正难的是气息、声压、咬字和情绪，能不能在最脆弱的地方同时稳住。", sans(37), 900)
        draw_lines(draw, (74, 588), lines, sans(37), (222, 211, 197, 255), 12)
        chips = ["气息长线", "情绪推进", "声压控制", "克制爆发"]
        x, y = 72, 1640
        for chip in chips:
            tw = text_w(draw, chip, sans(28))
            draw.rounded_rectangle((x, y, x + tw + 38, y + 60), radius=8, fill=(7, 8, 13, 168), outline=(201, 155, 85, 138), width=2)
            draw.text((x + 19, y + 12), chip, font=sans(28), fill=(241, 216, 170, 255))
            x += tw + 58
    return save("intro", painter)


def rank_overlay(item):
    accent = (255, 123, 131, 255) if item["no"] == "01" else (201, 155, 85, 255)

    def painter(draw):
        scrim(draw, True)
        draw.rounded_rectangle((66, 1254, 1014, 1708), radius=10, fill=(7, 8, 13, 208), outline=(255, 255, 255, 38), width=2)
        draw.rounded_rectangle((66, 1254, 76, 1708), radius=4, fill=accent)
        draw.text((104, 1300), f"第 {item['no']} 名", font=sans(31), fill=accent)
        draw.text((104, 1365), item["name"], font=serif(82), fill=(248, 244, 237, 255), stroke_width=1, stroke_fill=(0, 0, 0, 110))
        draw.text((104, 1478), item["tag"], font=sans(39), fill=accent)
        draw_lines(draw, (104, 1545), wrap(draw, item["note"], sans(30), 800), sans(30), (213, 202, 191, 255), 10)
    return save(f"rank_{item['key']}", painter)


def mini_overlay(item):
    accent = (255, 123, 131, 255) if item["no"] == "01" else (201, 155, 85, 255)

    def painter(draw):
        scrim(draw, False)
        tw = text_w(draw, item["plain"], serif(39))
        draw.rounded_rectangle((58, 96, 182 + tw, 166), radius=8, fill=(7, 8, 13, 190), outline=accent, width=2)
        draw.text((78, 104), item["no"], font=sans(44), fill=accent)
        draw.text((144, 109), item["plain"], font=serif(39), fill=(248, 244, 237, 255))
    return save(f"mini_{item['key']}", painter)


def outro_overlay():
    def painter(draw):
        scrim(draw, True)
        draw.text((72, 312), "最终榜单", font=sans(33), fill=(201, 155, 85, 255))
        y = draw_lines(draw, (72, 370), wrap(draw, "最难的不是唱哭，而是把脆弱唱稳。", serif(64), 920), serif(64), (248, 244, 237, 255), 12, 1)
        y += 48
        for item in reversed(ITEMS):
            accent = (255, 123, 131, 255) if item["no"] == "01" else (201, 155, 85, 255)
            draw.rounded_rectangle((72, y, 1008, y + 76), radius=8, fill=(7, 8, 13, 172), outline=(255, 255, 255, 42), width=2)
            draw.text((96, y + 9), item["no"], font=sans(39), fill=accent)
            tw = text_w(draw, item["plain"], serif(36))
            draw.text((984 - tw, y + 13), item["plain"], font=serif(36), fill=(248, 244, 237, 255))
            y += 92
        draw_lines(draw, (72, y + 28), wrap(draw, "从第五到第一：越过山丘、凉凉、一次就好、其实都没有、洋葱。越往前，越不是靠哭腔就能唱出来的难。", sans(31), 900), sans(31), (218, 208, 198, 255), 10)
    return save("outro", painter)


def cta_overlay():
    def painter(draw):
        draw.rounded_rectangle((78, 1638, 1002, 1808), radius=10, fill=(7, 8, 13, 194), outline=(201, 155, 85, 90), width=2)
        line1 = "为你的第一名，评论区投票"
        line2 = "点赞 · 收藏 · 关注"
        draw.text(((W - text_w(draw, line1, sans(45))) / 2, 1668), line1, font=sans(45), fill=(255, 123, 131, 255))
        draw.text(((W - text_w(draw, line2, sans(36))) / 2, 1743), line2, font=sans(36), fill=(201, 155, 85, 255))
    return save("cta", painter)


def overlay_video(src, overlay, out, media_start, length, dark=0.0):
    run([
        "ffmpeg", "-v", "error", "-i", str(src), "-i", str(overlay),
        "-filter_complex",
        f"[0:v]trim=start={media_start}:duration={length},setpts=PTS-STARTPTS,fps=30,scale={W}:{H},setsar=1,eq=brightness={dark}:saturation=.92[bg];"
        f"[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-t", str(length), "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", "-an", str(out), "-y",
    ])


def concat_segments(paths, out):
    S.mkdir(parents=True, exist_ok=True)
    lst = S / "video_list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in paths), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out), "-y"])


def main():
    timeline = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
    block_map = {b["key"]: b for b in timeline["blocks"]}
    R.mkdir(exist_ok=True)
    S.mkdir(parents=True, exist_ok=True)

    intro = intro_overlay()
    outro = outro_overlay()
    cta = cta_overlay()
    segs = []

    intro_seg = S / "seg_intro.mp4"
    overlay_video(C / "vert_yueguoshanqiu.mp4", intro, intro_seg, 0, timeline["intro_end"], dark=-0.16)
    segs.append(intro_seg)

    for item in ITEMS:
        block = block_map[item["key"]]
        card_len = q(block["full_start"] - block["start"])
        show_len = q(block["show"])
        clip = C / f"{item['clip']}.mp4"
        card = S / f"seg_{item['key']}_card.mp4"
        show = S / f"seg_{item['key']}_show.mp4"
        overlay_video(clip, rank_overlay(item), card, 0, card_len, dark=-0.22)
        overlay_video(clip, mini_overlay(item), show, card_len, show_len, dark=0.0)
        segs.extend([card, show])

    outro_len = q(timeline["total"] - timeline["outro_start"])
    cta_local = q(timeline["cta_voice"] - timeline["outro_start"] - 0.2)
    base_outro = S / "seg_outro_base.mp4"
    overlay_video(C / "vert_yangcong.mp4", outro, base_outro, 0, outro_len, dark=-0.20)
    outro_seg = S / "seg_outro.mp4"
    run([
        "ffmpeg", "-v", "error", "-i", str(base_outro), "-i", str(cta),
        "-filter_complex", f"[0:v][1:v]overlay=0:0:enable='gte(t,{cta_local})',format=yuv420p[v]",
        "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30",
        "-keyint_min", "30", "-pix_fmt", "yuv420p", "-an", str(outro_seg), "-y",
    ])
    segs.append(outro_seg)

    silent = R / "ff_video_silent.mp4"
    concat_segments(segs, silent)
    final = R / "yangzongwei-hardest-top5.mp4"
    run([
        "ffmpeg", "-v", "error", "-i", str(silent), "-i", "master.wav",
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(final), "-y",
    ])
    print("wrote", final, "video", dur(ROOT / "master.wav"), "s audio master")


if __name__ == "__main__":
    main()

