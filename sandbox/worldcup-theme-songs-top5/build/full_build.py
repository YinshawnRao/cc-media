#!/usr/bin/env python3
"""Build clips, master.wav, timeline metadata, and HyperFrames HTML."""
import contextlib
import html
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
AUDIO = ROOT / "audio"
CLIPS = ROOT / "clips"

LEAD = 0.35
DIG = 1.35
BED = 0.14
VOICE_GAIN = 2.0
PRE_ROLL = 1.5
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
OUTRO_TAIL = 2.8
DIGEST_O = 1.0

ITEMS = [
    {
        "key": "p5_time",
        "clip": "vert_time",
        "rank": "05",
        "song": "The Time of Our Lives",
        "artist": "Il Divo & Toni Braxton",
        "cup": "2006 德国世界杯",
        "label": "庄重收束",
        "tag": "歌剧流行 + R&B，把颁奖礼气质唱满",
        "raw": "time_yt_hd.mp4",
        "crop": "1920:1080:0:0",
        "target_onset": 159.6,
        "show": 30.0,
    },
    {
        "key": "p4_one",
        "clip": "vert_one",
        "rank": "04",
        "song": "We Are One (Ole Ola)",
        "artist": "Pitbull feat. Jennifer Lopez & Claudia Leitte",
        "cup": "2014 巴西世界杯",
        "label": "开幕派对",
        "tag": "明星阵容、鼓点、口号，全球一起开场",
        "raw": "one_yt.mp4",
        "crop": "1920:1080:0:0",
        "target_onset": 93.9,
        "show": 32.0,
    },
    {
        "key": "p3_estate",
        "clip": "vert_estate",
        "rank": "03",
        "song": "Un'estate italiana",
        "artist": "Edoardo Bennato & Gianna Nannini",
        "cup": "1990 意大利世界杯",
        "label": "老派浪漫",
        "tag": "意大利之夏的辽阔感，足球变成回忆",
        "raw": "estate_yt.mp4",
        "crop": "640:480:0:0",
        "target_onset": 180.3,
        "show": 31.0,
    },
    {
        "key": "p2_copa",
        "clip": "vert_copa",
        "rank": "02",
        "song": "La Copa de la Vida",
        "artist": "Ricky Martin",
        "cup": "1998 法国世界杯",
        "label": "现代模板",
        "tag": "拉丁节奏、体育口号、全场合唱的燃点",
        "raw": "copa_yt.mp4",
        "crop": "640:480:0:0",
        "target_onset": 65.0,
        "show": 32.0,
    },
    {
        "key": "p1_waka",
        "clip": "vert_waka",
        "rank": "01",
        "song": "Waka Waka (This Time for Africa)",
        "artist": "Shakira feat. Freshlyground",
        "cup": "2010 南非世界杯",
        "label": "综合第一",
        "tag": "主办地气质、传播度、感染力全部在线",
        "raw": "waka_yt.mp4",
        "crop": "1920:1080:0:0",
        "target_onset": 90.2,
        "show": 38.0,
    },
]


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def dur_wav(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def probe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
    )
    return float(out.decode().strip())


def make_vertical_clip(src, out, start, duration, crop, brightness="-0.31", saturation="1.07"):
    src = str(src)
    out_path = Path(out)
    if out_path.exists() and probe_duration(out_path) >= duration - 0.15:
        return
    out = str(out_path)
    vf = (
        f"[0:v]crop={crop},split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=34,eq=brightness={brightness}:saturation={saturation}[bgb];"
        "[fg]scale=1080:-2[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            src,
            "-ss",
            str(q(start)),
            "-t",
            str(q(duration)),
            "-filter_complex",
            vf,
            "-map",
            "[v]",
            "-map",
            "0:a",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-r",
            "30",
            "-g",
            "30",
            "-keyint_min",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            out,
            "-y",
        ]
    )


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    ramp = max(0.45, q(full_start_local - swell))
    return (
        f"(lt(t,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{ramp})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


def build_timeline():
    d_intro = dur_wav(AUDIO / "intro.wav")
    d_outro = dur_wav(AUDIO / "outro.wav")
    d_cta = dur_wav(AUDIO / "outro_cta.wav")
    for item in ITEMS:
        item["voice_dur"] = dur_wav(AUDIO / f"{item['key']}.wav")

    intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
    t = intro_end
    blocks = []
    for item in ITEMS:
        narr_start = q(t + LEAD)
        narr_end = q(narr_start + item["voice_dur"])
        full_start = q(narr_end + 0.25 + DIG)
        end = q(full_start + item["show"])
        full_start_local = q(full_start - t)
        raw_start = max(0, q(item["target_onset"] - (full_start_local - PRE_ROLL)))
        blocks.append(
            {
                **item,
                "start": q(t),
                "end": end,
                "narr_start": narr_start,
                "narr_end": narr_end,
                "full_start": full_start,
                "raw_start": raw_start,
                "clip_duration": q(end - t + 0.6),
            }
        )
        t = end

    outro_start = q(t)
    outro_voice = q(outro_start + LEAD)
    outro_voice_end = q(outro_voice + d_outro)
    cta_voice = q(outro_voice_end + DIGEST_O)
    cta_voice_end = q(cta_voice + d_cta)
    total = q(cta_voice_end + OUTRO_TAIL)

    return {
        "intro_end": intro_end,
        "outro_start": outro_start,
        "outro_voice": outro_voice,
        "outro_voice_end": outro_voice_end,
        "cta_voice": cta_voice,
        "cta_voice_end": cta_voice_end,
        "total": total,
        "blocks": blocks,
    }


def prepare_clips(tl):
    CLIPS.mkdir(parents=True, exist_ok=True)
    intro_duration = q(tl["intro_end"] + 0.6)
    make_vertical_clip(RAW / "one_yt.mp4", CLIPS / "vert_intro.mp4", 12.0, intro_duration, "1920:1080:0:0")
    for block in tl["blocks"]:
        make_vertical_clip(
            RAW / block["raw"],
            CLIPS / f"{block['clip']}.mp4",
            block["raw_start"],
            block["clip_duration"],
            block["crop"],
        )
    outro_duration = q(tl["total"] - tl["outro_start"] + 0.6)
    make_vertical_clip(RAW / "waka_yt.mp4", CLIPS / "vert_outro.mp4", 134.0, outro_duration, "1920:1080:0:0")


def build_audio(tl):
    segments = []

    intro_dur = tl["intro_end"]
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            "clips/vert_intro.mp4",
            "-i",
            "audio/intro.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={max(0.1, intro_dur-0.9)}:d=0.9[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95:level=false[out]",
            "-map",
            "[out]",
            "-ac",
            "2",
            "-ar",
            "48000",
            "seg_intro.wav",
            "-y",
        ]
    )
    segments.append("seg_intro.wav")

    for block in tl["blocks"]:
        seg_dur = q(block["end"] - block["start"])
        narr_end_local = q(LEAD + block["voice_dur"])
        full_start_local = q(block["full_start"] - block["start"])
        out = f"seg_{block['key']}.wav"
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                f"clips/{block['clip']}.mp4",
                "-i",
                f"audio/{block['key']}.wav",
                "-filter_complex",
                f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
                f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{envelope(narr_end_local, full_start_local)}':eval=frame[music];"
                f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95:level=false[out]",
                "-map",
                "[out]",
                "-ac",
                "2",
                "-ar",
                "48000",
                out,
                "-y",
            ]
        )
        segments.append(out)

    outro_dur = q(tl["total"] - tl["outro_start"])
    cta_local = q(tl["cta_voice"] - tl["outro_start"])
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            "clips/vert_outro.mp4",
            "-i",
            "audio/outro.wav",
            "-i",
            "audio/outro_cta.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
            f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
            f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.9,afade=t=out:st={max(0.1, outro_dur-1.6)}:d=1.6[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95:level=false[out]",
            "-map",
            "[out]",
            "-ac",
            "2",
            "-ar",
            "48000",
            "seg_outro.wav",
            "-y",
        ]
    )
    segments.append("seg_outro.wav")

    (ROOT / "seglist.txt").write_text("".join(f"file '{s}'\n" for s in segments), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])


def esc(value):
    return html.escape(str(value), quote=True)


def clip_div(idv, cls, start, duration, track, inner=""):
    return (
        f'<div id="{idv}" class="clip {cls}" data-start="{q(start)}" '
        f'data-duration="{q(duration)}" data-track-index="{track}">{inner}</div>'
    )


def build_html(tl):
    vids = [
        (0.0, tl["intro_end"], "vert_intro"),
        *[(b["start"], q(b["end"] - b["start"]), b["clip"]) for b in tl["blocks"]],
        (tl["outro_start"], q(tl["total"] - tl["outro_start"]), "vert_outro"),
    ]
    video_html = []
    for i, (start, duration, clip) in enumerate(vids):
        track = 0 if i % 2 == 0 else 6
        video_html.append(
            f'<video id="v{i}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
            f'data-track-index="{track}" src="clips/{clip}.mp4" muted playsinline></video>'
        )

    cards = []
    tweens = []
    wipe_times = [tl["intro_end"], *[b["start"] for b in tl["blocks"][1:]], tl["outro_start"]]
    for idx, b in enumerate(tl["blocks"]):
        card_start = q(b["start"] + 0.18)
        card_dur = q(max(1.0, b["full_start"] - card_start - 0.12))
        mini_start = b["full_start"]
        mini_dur = q(b["end"] - b["full_start"])
        safe_song = esc(b["song"])
        safe_artist = esc(b["artist"])
        safe_cup = esc(b["cup"])
        safe_label = esc(b["label"])
        safe_tag = esc(b["tag"])
        card_id = f"card{idx}"
        mini_id = f"mini{idx}"
        rank_cls = " first" if b["rank"] == "01" else ""
        cards.append(
            clip_div(
                card_id,
                f"songCard{rank_cls}",
                card_start,
                card_dur,
                2,
                f'<div class="rank">{b["rank"]}</div>'
                f'<div class="meta">{safe_cup}</div>'
                f'<div class="song">{safe_song}</div>'
                f'<div class="artist">{safe_artist}</div>'
                f'<div class="tag">{safe_label} · {safe_tag}</div>',
            )
        )
        cards.append(
            clip_div(
                mini_id,
                f"miniLabel{rank_cls}",
                mini_start,
                mini_dur,
                4,
                f'<span class="rank">{b["rank"]}</span><span class="song">{safe_song}</span><span class="cup">{safe_cup}</span>',
            )
        )
        tweens.extend(
            [
                f'tl.fromTo("#{card_id} .rank", {{x:-70, opacity:0, scale:.94}}, {{x:0, opacity:1, scale:1, duration:.55, ease:"expo.out"}}, {q(card_start+0.08)});',
                f'tl.fromTo("#{card_id} .meta", {{y:28, opacity:0}}, {{y:0, opacity:1, duration:.45, ease:"power3.out"}}, {q(card_start+0.24)});',
                f'tl.fromTo("#{card_id} .song", {{y:42, opacity:0}}, {{y:0, opacity:1, duration:.62, ease:"power4.out"}}, {q(card_start+0.38)});',
                f'tl.fromTo("#{card_id} .artist", {{y:24, opacity:0}}, {{y:0, opacity:1, duration:.48, ease:"power2.out"}}, {q(card_start+0.62)});',
                f'tl.fromTo("#{card_id} .tag", {{x:38, opacity:0}}, {{x:0, opacity:1, duration:.45, ease:"back.out(1.25)"}}, {q(card_start+0.82)});',
                f'tl.to("#{card_id}", {{opacity:0, duration:.34, ease:"power2.in"}}, {q(card_start+card_dur-0.36)});',
                f'tl.set("#{card_id}", {{opacity:0}}, {q(card_start+card_dur)});',
                f'tl.fromTo("#{mini_id}", {{x:-36, opacity:0}}, {{x:0, opacity:1, duration:.45, ease:"power3.out"}}, {q(mini_start+0.05)});',
            ]
        )

    cover = clip_div(
        "cover",
        "",
        0,
        tl["intro_end"],
        2,
        '<div class="coverTop">官方歌曲 · 时代记忆 · 全球合唱</div>'
        '<div class="coverTitle"><span>世界杯</span><b>最佳主题曲</b><em>TOP 5</em></div>'
        '<div class="coverRule"></div>'
        '<div class="coverSub">从闭幕式史诗，到全世界都会唱的副歌</div>',
    )
    outro = clip_div(
        "outro",
        "",
        tl["outro_voice"],
        q(tl["cta_voice"] - tl["outro_voice"]),
        4,
        '<div class="outroK">世界杯主题曲真正难的</div>'
        '<div class="outroTitle">是让不同语言的人<br>同时跟上同一个节奏</div>'
        '<div class="outroLine"></div>',
    )
    cta = clip_div(
        "cta",
        "",
        q(tl["cta_voice"] - 0.15),
        q(tl["total"] - tl["cta_voice"] + 0.15),
        5,
        '<div class="ctaVote">你最想为哪一首投票？</div>'
        '<div class="ctaFollow">点赞 · 收藏 · 关注</div>',
    )
    scrim = clip_div("scrim", "", 0, tl["total"], 1)
    audio = f'<audio id="master" class="clip" data-start="0" data-duration="{tl["total"]}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

    wipe_js = []
    for t in wipe_times:
        wipe_js.append(
            f'tl.set("#wipeA", {{x:-1080}}, {q(t-0.01)});'
            f'tl.set("#wipeB", {{x:-1080}}, {q(t-0.01)});'
            f'tl.to("#wipeA", {{x:0, duration:.22, ease:"power3.inOut"}}, {q(t)});'
            f'tl.to("#wipeB", {{x:0, duration:.22, ease:"power3.inOut"}}, {q(t+0.05)});'
            f'tl.to("#wipeA", {{x:1080, duration:.24, ease:"power3.inOut"}}, {q(t+0.27)});'
            f'tl.to("#wipeB", {{x:1080, duration:.24, ease:"power3.inOut"}}, {q(t+0.33)});'
        )

    css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07100b;font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif;color:#f5f0df}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07100b}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:radial-gradient(circle at 20% 10%,rgba(216,170,69,.30),rgba(7,16,11,0) 34%),linear-gradient(180deg,rgba(7,16,11,.64) 0%,rgba(7,16,11,.10) 32%,rgba(7,16,11,.22) 58%,rgba(7,16,11,.86) 100%)}
#grain{position:absolute;inset:-80px;z-index:2;pointer-events:none;opacity:.16;background-image:repeating-linear-gradient(0deg,rgba(245,240,223,.10) 0 1px,rgba(7,16,11,0) 1px 3px)}
#wipeA,#wipeB{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:20;pointer-events:none}
#wipeA{background:#d8aa45}
#wipeB{background:#e33d2f;clip-path:polygon(0 0,100% 0,82% 100%,0 100%)}
#cover{position:absolute;inset:0;z-index:5;padding:150px 78px 130px;display:flex;flex-direction:column;justify-content:flex-end}
.coverTop{position:absolute;top:120px;left:78px;font:700 30px "JetBrains Mono";letter-spacing:.12em;color:#d8aa45}
.coverTitle{font-family:"Noto Serif SC";font-weight:900;line-height:.96;text-shadow:0 18px 60px rgba(0,0,0,.42)}
.coverTitle span{display:block;font-size:94px;color:#f5f0df}
.coverTitle b{display:block;font-size:130px;color:#f5f0df}
.coverTitle em{display:block;margin-top:18px;font:900 176px "JetBrains Mono";font-style:normal;color:#d8aa45;letter-spacing:-.05em}
.coverRule{width:248px;height:9px;margin-top:34px;background:#e33d2f;border-radius:999px;box-shadow:0 0 30px rgba(227,61,47,.42)}
.coverSub{max-width:820px;margin-top:34px;font-size:42px;font-weight:700;line-height:1.36;color:#d8e6e0}
.songCard{position:absolute;left:70px;right:70px;bottom:178px;z-index:6;color:#f5f0df}
.songCard .rank{font:900 168px/0.85 "JetBrains Mono";color:#d8aa45;letter-spacing:-.08em;text-shadow:0 16px 48px rgba(0,0,0,.45)}
.songCard.first .rank{color:#e33d2f;text-shadow:0 0 42px rgba(227,61,47,.44)}
.songCard .meta{margin-top:24px;font:900 34px "JetBrains Mono";letter-spacing:.08em;color:#d8e6e0}
.songCard .song{margin-top:18px;font:900 78px/1.05 "Noto Serif SC";max-width:900px;color:#f5f0df}
.songCard .artist{margin-top:18px;font-size:32px;font-weight:700;line-height:1.25;color:#b7b6a5;max-width:880px}
.songCard .tag{display:inline-flex;margin-top:28px;padding:15px 22px;border-left:8px solid #e33d2f;background:rgba(13,26,19,.78);font-size:32px;font-weight:800;line-height:1.28;color:#f5f0df;box-shadow:0 18px 55px rgba(0,0,0,.30)}
.miniLabel{position:absolute;left:56px;right:56px;top:84px;z-index:6;display:flex;align-items:center;gap:18px;padding:16px 20px;background:rgba(7,16,11,.70);border:2px solid rgba(216,170,69,.56);backdrop-filter:blur(14px);color:#f5f0df}
.miniLabel .rank{font:900 50px "JetBrains Mono";color:#d8aa45}
.miniLabel.first .rank{color:#e33d2f}
.miniLabel .song{font:900 34px "Noto Serif SC";white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:610px}
.miniLabel .cup{margin-left:auto;font:700 22px "JetBrains Mono";letter-spacing:.04em;color:#d8e6e0}
#outro{position:absolute;left:70px;right:70px;bottom:286px;z-index:6;color:#f5f0df}
.outroK{font:900 34px "JetBrains Mono";letter-spacing:.09em;color:#d8aa45}
.outroTitle{margin-top:24px;font:900 76px/1.16 "Noto Serif SC";color:#f5f0df;text-shadow:0 18px 58px rgba(0,0,0,.42)}
.outroLine{width:220px;height:8px;margin-top:34px;background:#e33d2f;border-radius:999px}
#cta{position:absolute;left:70px;right:70px;bottom:154px;z-index:7;color:#f5f0df}
.ctaVote{font:900 58px/1.15 "Noto Serif SC";color:#f5f0df}
.ctaFollow{display:inline-flex;margin-top:22px;padding:14px 22px;background:#d8aa45;color:#07100b;font-size:34px;font-weight:900;letter-spacing:.08em}
"""
    body = "\n".join(video_html)
    body += "\n" + scrim + '\n<div id="grain"></div>\n<div id="wipeA"></div><div id="wipeB"></div>\n'
    body += cover + "\n" + "\n".join(cards) + "\n" + outro + "\n" + cta + "\n" + audio

    js = f"""
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
tl.set("#wipeA", {{x:-1080}}, 0);
tl.set("#wipeB", {{x:-1080}}, 0);
tl.fromTo("#grain", {{x:0,y:0}}, {{x:-54,y:-38,duration:{tl["total"]},ease:"none"}}, 0);
tl.fromTo("#cover .coverTop", {{x:-44,opacity:0}}, {{x:0,opacity:1,duration:.55,ease:"power3.out"}}, .24);
tl.fromTo("#cover .coverTitle span", {{y:42,opacity:0}}, {{y:0,opacity:1,duration:.58,ease:"power4.out"}}, .46);
tl.fromTo("#cover .coverTitle b", {{y:54,opacity:0}}, {{y:0,opacity:1,duration:.70,ease:"expo.out"}}, .66);
tl.fromTo("#cover .coverTitle em", {{x:-72,opacity:0,scale:.94}}, {{x:0,opacity:1,scale:1,duration:.72,ease:"back.out(1.2)"}}, .92);
tl.fromTo("#cover .coverRule", {{scaleX:0,transformOrigin:"left"}}, {{scaleX:1,duration:.50,ease:"power3.inOut"}}, 1.38);
tl.fromTo("#cover .coverSub", {{y:24,opacity:0}}, {{y:0,opacity:1,duration:.54,ease:"power2.out"}}, 1.58);
tl.to("#cover", {{opacity:0,duration:.36,ease:"power2.in"}}, {q(tl["intro_end"]-.42)});
tl.set("#cover", {{opacity:0}}, {q(tl["intro_end"])});
{chr(10).join(wipe_js)}
{chr(10).join(tweens)}
tl.fromTo("#outro .outroK", {{x:-32,opacity:0}}, {{x:0,opacity:1,duration:.55,ease:"power3.out"}}, {q(tl["outro_voice"]+.10)});
tl.fromTo("#outro .outroTitle", {{y:44,opacity:0}}, {{y:0,opacity:1,duration:.76,ease:"expo.out"}}, {q(tl["outro_voice"]+.42)});
tl.fromTo("#outro .outroLine", {{scaleX:0,transformOrigin:"left"}}, {{scaleX:1,duration:.48,ease:"power3.inOut"}}, {q(tl["outro_voice"]+1.10)});
tl.to("#outro", {{opacity:0,duration:.32,ease:"power2.in"}}, {q(tl["cta_voice"]-.35)});
tl.set("#outro", {{opacity:0}}, {q(tl["cta_voice"])});
tl.fromTo("#cta .ctaVote", {{y:32,opacity:0}}, {{y:0,opacity:1,duration:.58,ease:"power3.out"}}, {q(tl["cta_voice"])});
tl.fromTo("#cta .ctaFollow", {{x:-28,opacity:0}}, {{x:0,opacity:1,duration:.46,ease:"back.out(1.35)"}}, {q(tl["cta_voice"]+.42)});
window.__timelines["main"]=tl;
"""
    document = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{tl["total"]}" data-width="1080" data-height="1920">
{body}
  </div>
  <script>{js}</script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(document, encoding="utf-8")


def main():
    tl = build_timeline()
    prepare_clips(tl)
    build_audio(tl)
    build_html(tl)
    (ROOT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    master_dur = probe_duration(ROOT / "master.wav")
    print("planned total:", tl["total"])
    print("master dur:", round(master_dur, 3))
    for b in tl["blocks"]:
        print(
            f"{b['rank']} {b['song']}: raw_start={b['raw_start']:.2f}, "
            f"target_onset_local={b['target_onset']-b['raw_start']:.2f}, full_start_local={b['full_start']-b['start']:.2f}, show={b['show']}"
        )


if __name__ == "__main__":
    main()
