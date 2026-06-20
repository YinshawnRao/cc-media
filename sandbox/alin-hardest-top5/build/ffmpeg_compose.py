#!/usr/bin/env python3
"""Offline FFmpeg compositor for the A-Lin top 5 video.

This path is used when HyperFrames cannot bind a local preview server inside
the sandbox. Text overlays are rendered to transparent PNGs with Pillow, then
FFmpeg composites the existing 1080x1920 clips and post-muxes master.wav.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
O = ROOT / "overlays"
R = ROOT / "renders"
S = R / "ff_segments"
W, H = 1080, 1920

SHOW_DEFAULT = 36.0
SHOW_MAP = {
    "p5_guilty": 32.0,
    "p4_sorrow": 34.0,
    "p3_happiness": 34.0,
}
LEAD = 0.35
DIG = 1.5
INTRO_VOICE_START = 0.45
INTRO_GAP = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0

FONT_SANS = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
FONT_SERIF = Path("/System/Library/Fonts/Supplemental/Songti.ttc")
if not FONT_SERIF.exists():
    FONT_SERIF = FONT_SANS
if not FONT_SANS.exists():
    FONT_SANS = Path("/System/Library/Fonts/STHeiti Medium.ttc")


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def ff_font(path, size):
    return ImageFont.truetype(str(path), size)


def sans(size):
    return ff_font(FONT_SANS, size)


def serif(size):
    return ff_font(FONT_SERIF, size)


def text_w(draw, text, font):
    if not text:
        return 0
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap(draw, text, font, max_width):
    lines = []
    current = ""
    for ch in text:
        trial = current + ch
        if current and text_w(draw, trial, font) > max_width:
            lines.append(current)
            current = ch.lstrip()
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw_lines(draw, xy, lines, font, fill, gap=8, stroke=0, stroke_fill=(0, 0, 0, 0)):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        box = draw.textbbox((x, y), line, font=font, stroke_width=stroke)
        y = box[3] + gap
    return y


def save_overlay(name, painter):
    O.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    painter(draw)
    path = O / f"{name}.png"
    img.save(path)
    return path


def shadow_panel(draw, xyxy, alpha=188, accent=(217, 163, 95, 255)):
    x0, y0, x1, y1 = xyxy
    draw.rounded_rectangle(xyxy, radius=10, fill=(7, 8, 12, alpha), outline=(255, 255, 255, 38), width=2)
    draw.rounded_rectangle((x0, y0, x0 + 8, y1), radius=4, fill=accent)


def paint_scrim(draw):
    for y in range(H):
        top = int(170 * max(0, 1 - y / 720))
        bottom = int(180 * max(0, (y - 1050) / 870))
        mid = 24
        a = min(210, max(top, bottom, mid))
        draw.line((0, y, W, y), fill=(7, 8, 12, a))


def make_intro():
    def painter(draw):
        paint_scrim(draw)
        draw.rounded_rectangle((72, 148, 405, 204), radius=8, fill=(7, 8, 12, 142), outline=(217, 163, 95, 122), width=2)
        draw.rectangle((94, 174, 146, 178), fill=(217, 163, 95, 255))
        draw.text((164, 155), "声乐难度盘点", font=sans(30), fill=(217, 163, 95, 255))
        draw.text((70, 270), "黄丽玲 A-Lin", font=serif(106), fill=(248, 243, 238, 255), stroke_width=2, stroke_fill=(0, 0, 0, 120))
        draw.text((70, 392), "最难的5首歌", font=serif(128), fill=(248, 243, 238, 255), stroke_width=2, stroke_fill=(0, 0, 0, 120))
        lines = wrap(draw, "不只比高音。真正难的是大嗓情歌里的细节、长线支撑和情绪控制。", sans(38), 850)
        draw_lines(draw, (74, 560), lines, sans(38), (216, 206, 196, 255), gap=12)
        chips = ["高位持续", "长句气息", "声压控制", "克制情绪", "大歌气场"]
        x, y = 72, 1638
        for chip in chips:
            tw = text_w(draw, chip, sans(29))
            draw.rounded_rectangle((x, y, x + tw + 38, y + 60), radius=8, fill=(7, 8, 12, 166), outline=(217, 163, 95, 138), width=2)
            draw.text((x + 19, y + 12), chip, font=sans(29), fill=(241, 210, 171, 255))
            x += tw + 58
            if x > 820:
                x, y = 72, y + 78

    return save_overlay("intro", painter)


def make_full_label(item):
    accent = (255, 106, 92, 255) if item["no"] == "01" else (217, 163, 95, 255)

    def painter(draw):
        paint_scrim(draw)
        shadow_panel(draw, (68, 1284, 1012, 1698), 196, accent)
        draw.text((104, 1326), f"第 {item['no']} 名", font=sans(31), fill=accent)
        draw.text((104, 1386), item["name"], font=serif(78), fill=(248, 243, 238, 255), stroke_width=1, stroke_fill=(0, 0, 0, 96))
        draw.text((104, 1492), item["tag"], font=sans(40), fill=accent)
        lines = wrap(draw, item["note"], sans(30), 805)
        draw_lines(draw, (104, 1560), lines, sans(30), (213, 203, 193, 255), gap=10)

    return save_overlay(f"full_{item['key']}", painter)


def make_mini_label(item):
    accent = (255, 106, 92, 255) if item["no"] == "01" else (217, 163, 95, 255)

    def painter(draw):
        paint_scrim(draw)
        label = item["plain"]
        tw = text_w(draw, label, serif(39))
        draw.rounded_rectangle((58, 96, 180 + tw, 166), radius=8, fill=(7, 8, 12, 184), outline=accent, width=2)
        draw.text((78, 104), item["no"], font=sans(44), fill=accent)
        draw.text((144, 109), label, font=serif(39), fill=(248, 243, 238, 255))

    return save_overlay(f"mini_{item['key']}", painter)


def make_outro(blocks):
    rows = list(reversed(blocks))

    def painter(draw):
        paint_scrim(draw)
        draw.text((72, 326), "最终榜单", font=sans(33), fill=(217, 163, 95, 255))
        lines = wrap(draw, "阿林的难，不只是嗓门大，是每一次爆发都还留着控制。", serif(64), 920)
        y = draw_lines(draw, (72, 385), lines, serif(64), (248, 243, 238, 255), gap=12, stroke=1, stroke_fill=(0, 0, 0, 110))
        y += 42
        for row in rows:
            draw.rounded_rectangle((72, y, 1008, y + 76), radius=8, fill=(7, 8, 12, 168), outline=(255, 255, 255, 38), width=2)
            accent = (255, 106, 92, 255) if row["no"] == "01" else (217, 163, 95, 255)
            draw.text((96, y + 9), row["no"], font=sans(39), fill=accent)
            tw = text_w(draw, row["plain"], serif(36))
            draw.text((984 - tw, y + 13), row["plain"], font=serif(36), fill=(248, 243, 238, 255))
            y += 92
        close = "这五首从早期强声压，到电影主题曲的细腻克制，再到压轴的大嗓情歌，刚好串起她最难被模仿的那一面。"
        draw_lines(draw, (72, y + 28), wrap(draw, close, sans(31), 900), sans(31), (216, 206, 196, 255), gap=10)

    return save_overlay("outro", painter)


def make_cta():
    def painter(draw):
        draw.rounded_rectangle((78, 1638, 1002, 1808), radius=10, fill=(7, 8, 12, 184), outline=(217, 163, 95, 82), width=2)
        line1 = "为你的第一名，评论区投票"
        line2 = "点赞 · 收藏 · 关注"
        draw.text(((W - text_w(draw, line1, sans(46))) / 2, 1668), line1, font=sans(46), fill=(255, 106, 92, 255))
        draw.text(((W - text_w(draw, line2, sans(36))) / 2, 1743), line2, font=sans(36), fill=(217, 163, 95, 255))

    return save_overlay("cta", painter)


items = [
    {"key": "p5_guilty", "clip": "vert_guilty", "no": "05", "name": "《失恋无罪》", "plain": "失恋无罪", "tag": "强声压和情绪爆发", "note": "早期招牌歌，厚声线、咬字、爆发都要稳"},
    {"key": "p4_sorrow", "clip": "vert_sorrow", "no": "04", "name": "《有一种悲伤》", "plain": "有一种悲伤", "tag": "克制比哭出来更难", "note": "不能太满，也不能太平，后段支撑很吃控制"},
    {"key": "p3_happiness", "clip": "vert_happiness", "no": "03", "name": "《幸福了 然后呢》", "plain": "幸福了 然后呢", "tag": "长线情绪慢慢堆高", "note": "压抑、迷惑、质问，一层一层往上推"},
    {"key": "p2_tian", "clip": "vert_tian", "no": "02", "name": "《天若有情》", "plain": "天若有情", "tag": "影视主题曲式的大气场", "note": "长句、开阔旋律、宿命感都要撑住"},
    {"key": "p1_reason", "clip": "vert_reason", "no": "01", "name": "《给我一个理由忘记》", "plain": "给我一个理由忘记", "tag": "K歌很红，真唱很难", "note": "高位持续、长句多，爆发和控制同时在线"},
]

for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    show = SHOW_MAP.get(item["key"], SHOW_DEFAULT)
    end = q(full_start + show)
    blocks.append({**item, "start": q(t), "end": end, "full_start": full_start, "show": show})
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
planned_total = q(cta_voice + d_cta + OUTRO_TAIL)
total = dur(ROOT / "master.wav")


def render_segment(name, clip, duration, overlays):
    S.mkdir(parents=True, exist_ok=True)
    out = S / f"{name}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(C / f"{clip}.mp4")]
    for overlay, _, _ in overlays:
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{duration:.3f}", "-i", str(overlay)]
    filters = [
        f"[0:v]trim=0:{duration:.3f},setpts=PTS-STARTPTS,fps=30,scale={W}:{H},setsar=1,format=rgba[base0]"
    ]
    current = "base0"
    for idx, (_, start, end) in enumerate(overlays, start=1):
        ov = f"ov{idx}"
        nxt = f"base{idx}"
        filters.append(f"[{idx}:v]format=rgba[{ov}]")
        filters.append(
            f"[{current}][{ov}]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'[{nxt}]"
        )
        current = nxt
    filters.append(f"[{current}]format=yuv420p[v]")
    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out),
    ]
    run(cmd)
    return out


def main():
    R.mkdir(parents=True, exist_ok=True)
    intro_overlay = make_intro()
    outro_overlay = make_outro(blocks)
    cta_overlay = make_cta()
    full = {b["key"]: make_full_label(b) for b in blocks}
    mini = {b["key"]: make_mini_label(b) for b in blocks}

    segment_paths = []
    segment_paths.append(render_segment("00_intro", "vert_intro", intro_end, [(intro_overlay, 0, intro_end)]))
    for idx, b in enumerate(blocks, start=1):
        seg_dur = q(b["end"] - b["start"])
        full_local = q(b["full_start"] - b["start"])
        segment_paths.append(
            render_segment(
                f"{idx:02d}_{b['key']}",
                b["clip"],
                seg_dur,
                [(full[b["key"]], 0, full_local), (mini[b["key"]], full_local, seg_dur + 0.2)],
            )
        )
    outro_dur = q(total - outro_start)
    cta_local = q(cta_voice - outro_start - 0.2)
    segment_paths.append(
        render_segment(
            "06_outro",
            "vert_reason",
            outro_dur,
            [(outro_overlay, 0, outro_dur + 0.2), (cta_overlay, cta_local, outro_dur + 0.2)],
        )
    )

    list_path = R / "video_segments.txt"
    list_path.write_text("".join(f"file '{p.resolve()}'\n" for p in segment_paths), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(R / "video_noaudio.mp4")])
    run([
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(R / "video_noaudio.mp4"),
        "-i",
        str(ROOT / "master.wav"),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(R / "alin-hardest-top5.mp4"),
    ])
    (R / "ffmpeg_schedule.json").write_text(
        json.dumps(
            {
                "duration": total,
                "planned_total": planned_total,
                "intro_end": intro_end,
                "blocks": blocks,
                "outro_start": outro_start,
                "cta_voice": cta_voice,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("rendered", R / "alin-hardest-top5.mp4", "duration", total)


if __name__ == "__main__":
    main()
