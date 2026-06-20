#!/usr/bin/env python3
"""Offline FFmpeg compositor for 王菲最难的5首歌.

HyperFrames source remains index.html; this fallback produces the deliverable
when the local browser/file-server render path is unavailable.
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
    {"key": "p5_kaidao", "clip": "vert_kaidao", "no": "05", "name": "《开到荼蘼》", "plain": "开到荼蘼", "tag": "冷、倔、锋利之间的平衡", "note": "副歌有推力但不能吼，锋芒不能显得用力"},
    {"key": "p4_bianhua", "clip": "vert_bianhua", "no": "04", "name": "《彼岸花》", "plain": "彼岸花", "tag": "越轻越难有支点", "note": "长线条、宿命感、气息和尾音都要干净"},
    {"key": "p3_hanwuji", "clip": "vert_hanwuji", "no": "03", "name": "《寒武纪》", "plain": "寒武纪", "tag": "难在克制，难在唱对", "note": "冷、悬、远，情绪不能太满也不能空掉"},
    {"key": "p2_duodeta", "clip": "vert_duodeta", "no": "02", "name": "《多得他》", "plain": "多得他", "tag": "R and B 律动和气息弹性", "note": "每一句都要有 groove，轻盈但不能薄"},
    {"key": "p1_face", "clip": "vert_face", "no": "01", "name": "《脸》", "plain": "脸", "tag": "类美声腔体，但不能学院派", "note": "圆、厚、立体，还要保留轻、冷、飘"},
]


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def font(path, size):
    return ImageFont.truetype(str(path), size)


def sans(size):
    return font(FONT_SANS, size)


def serif(size):
    return font(FONT_SERIF, size)


def text_w(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw, text, fnt, max_width):
    lines = []
    cur = ""
    for ch in text:
        trial = cur + ch
        if cur and text_w(draw, trial, fnt) > max_width:
            lines.append(cur)
            cur = ch.lstrip()
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, xy, lines, fnt, fill, gap=10, stroke=0):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 120))
        box = draw.textbbox((x, y), line, font=fnt, stroke_width=stroke)
        y = box[3] + gap
    return y


def scrim(draw, strong=False):
    for y in range(H):
        top = int((210 if strong else 160) * max(0, 1 - y / 720))
        bottom = int((215 if strong else 180) * max(0, (y - 1040) / 880))
        mid = 40 if strong else 24
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
        draw.text((600, 1478), "FAYE\nWONG", font=serif(142), fill=(248, 244, 237, 24), align="right")
        draw.rounded_rectangle((72, 148, 405, 204), radius=8, fill=(7, 8, 13, 150), outline=(216, 181, 106, 140), width=2)
        draw.rectangle((94, 174, 146, 178), fill=(216, 181, 106, 255))
        draw.text((164, 155), "声乐难度盘点", font=sans(30), fill=(216, 181, 106, 255))
        draw.text((70, 270), "王菲", font=serif(118), fill=(248, 244, 237, 255), stroke_width=2, stroke_fill=(0, 0, 0, 120))
        draw.text((70, 405), "最难的5首歌", font=serif(125), fill=(248, 244, 237, 255), stroke_width=2, stroke_fill=(0, 0, 0, 120))
        lines = wrap(draw, "不只看高音。真正难的是音准、气息、共鸣、律动，以及那种轻到快消失、却稳稳落地的控制力。", sans(37), 900)
        draw_lines(draw, (74, 585), lines, sans(37), (216, 207, 197, 255), 12)
        chips = ["音准控制", "腔体共鸣", "R and B 律动", "寓言感", "冷感锋芒"]
        x, y = 72, 1638
        for chip in chips:
            tw = text_w(draw, chip, sans(28))
            draw.rounded_rectangle((x, y, x + tw + 38, y + 60), radius=8, fill=(7, 8, 13, 168), outline=(216, 181, 106, 138), width=2)
            draw.text((x + 19, y + 12), chip, font=sans(28), fill=(240, 217, 168, 255))
            x += tw + 58
            if x > 820:
                x, y = 72, y + 78
    return save("intro", painter)


def rank_overlay(item):
    accent = (255, 118, 131, 255) if item["no"] == "01" else (216, 181, 106, 255)

    def painter(draw):
        scrim(draw, True)
        draw.rounded_rectangle((68, 1260, 1012, 1704), radius=10, fill=(7, 8, 13, 206), outline=(255, 255, 255, 38), width=2)
        draw.rounded_rectangle((68, 1260, 76, 1704), radius=4, fill=accent)
        draw.text((104, 1305), f"第 {item['no']} 名", font=sans(31), fill=accent)
        draw.text((104, 1368), item["name"], font=serif(82), fill=(248, 244, 237, 255), stroke_width=1, stroke_fill=(0, 0, 0, 110))
        draw.text((104, 1478), item["tag"], font=sans(39), fill=accent)
        draw_lines(draw, (104, 1545), wrap(draw, item["note"], sans(30), 800), sans(30), (211, 201, 191, 255), 10)
    return save(f"rank_{item['key']}", painter)


def mini_overlay(item):
    accent = (255, 118, 131, 255) if item["no"] == "01" else (216, 181, 106, 255)

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
        draw.text((72, 312), "最终榜单", font=sans(33), fill=(216, 181, 106, 255))
        y = draw_lines(draw, (72, 370), wrap(draw, "王菲最难的地方，是她看起来很轻，其实每一个音都站得很稳。", serif(64), 920), serif(64), (248, 244, 237, 255), 12, 1)
        y += 44
        for item in reversed(ITEMS):
            accent = (255, 118, 131, 255) if item["no"] == "01" else (216, 181, 106, 255)
            draw.rounded_rectangle((72, y, 1008, y + 76), radius=8, fill=(7, 8, 13, 170), outline=(255, 255, 255, 42), width=2)
            draw.text((96, y + 9), item["no"], font=sans(39), fill=accent)
            tw = text_w(draw, item["plain"], serif(36))
            draw.text((984 - tw, y + 13), item["plain"], font=serif(36), fill=(248, 244, 237, 255))
            y += 92
        draw_lines(draw, (72, y + 28), wrap(draw, "从第五到第一：开到荼蘼、彼岸花、寒武纪、多得他、脸。越往前，越不是靠模仿空灵能唱出来的难。", sans(31), 900), sans(31), (216, 207, 197, 255), 10)
    return save("outro", painter)


def cta_overlay():
    def painter(draw):
        draw.rounded_rectangle((78, 1638, 1002, 1808), radius=10, fill=(7, 8, 13, 190), outline=(216, 181, 106, 88), width=2)
        line1 = "为你的第一名，评论区投票"
        line2 = "点赞 · 收藏 · 关注"
        draw.text(((W - text_w(draw, line1, sans(45))) / 2, 1668), line1, font=sans(45), fill=(255, 118, 131, 255))
        draw.text(((W - text_w(draw, line2, sans(36))) / 2, 1743), line2, font=sans(36), fill=(216, 181, 106, 255))
    return save("cta", painter)


def overlay_video(src, overlay, out, length, dark=0.0, tail=0.0):
    video = f"[0:v]trim=0:{length},setpts=PTS-STARTPTS"
    if tail:
        video += f",tpad=stop_mode=clone:stop_duration={tail}"
    video += f",fps=30,scale={W}:{H},setsar=1"
    if dark:
        video += f",eq=brightness={dark}:saturation=.88"
    video += "[bg]"
    out_len = q(length + tail)
    run([
        "ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", str(src), "-i", str(overlay),
        "-filter_complex", f"{video};[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-t", str(out_len), "-c:v", "libx264", "-preset", "veryfast",
        "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", "-an", str(out), "-y",
    ])


def concat_segments(paths, out):
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
    face_bg = C / "vert_face.mp4"
    intro_seg = S / "seg_intro.mp4"
    overlay_video(face_bg, intro, intro_seg, timeline["intro_end"], dark=-0.18)
    segs.append(intro_seg)

    for item in ITEMS:
        block = block_map[item["key"]]
        card_len = q(block["full_start"] - block["start"])
        show_len = q(block["show_end"] - block["full_start"])
        tail = q(block["end"] - block["show_end"])
        clip = C / f"{item['clip']}.mp4"
        card = S / f"seg_{item['key']}_card.mp4"
        show = S / f"seg_{item['key']}_show.mp4"
        overlay_video(clip, rank_overlay(item), card, card_len, dark=-0.25)
        overlay_video(clip, mini_overlay(item), show, show_len, dark=0.0, tail=tail)
        segs.extend([card, show])

    outro_len = q(timeline["total"] - timeline["outro_start"])
    cta_local = q(timeline["cta_voice"] - timeline["outro_start"] - 0.2)
    base_outro = S / "seg_outro_base.mp4"
    overlay_video(face_bg, outro, base_outro, outro_len, dark=-0.22)
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
    final = R / "wangfei-hardest-top5.mp4"
    run([
        "ffmpeg", "-v", "error", "-i", str(silent), "-i", "master.wav",
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(final), "-y",
    ])
    print("wrote", final)
    print(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-show_entries", "stream=width,height,codec_name,codec_type,channels",
        "-of", "json", str(final),
    ], cwd=ROOT).decode())


if __name__ == "__main__":
    main()
