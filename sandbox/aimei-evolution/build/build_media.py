#!/usr/bin/env python3
"""Build vertical clips, mixed audio, timeline metadata, and index.html."""

from __future__ import annotations

import json
import html as html_lib
import math
import shlex
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
RAW = PROJECT / "raw"
CLIPS = PROJECT / "clips"
AUDIO = PROJECT / "audio"
TMP = PROJECT / "probe" / "tmp_media"
TIMELINE = PROJECT / "timeline.json"
INDEX = PROJECT / "index.html"

LEAD = 0.25
POST = 1.0

SECTIONS = [
    {
        "id": "intro",
        "voice": "intro",
        "raw": "faye_hires_bilibili.mp4",
        "src_start": 0.0,
        "crop": "1620:860:0:160",
        "show": 0.0,
        "kind": "hook",
        "rank": "",
        "title": "华语乐坛到底有多少首《暧昧》？",
        "artist": "",
        "tag": "你第一反应是谁？",
        "quote": "同样叫《暧昧》，每一代人唱的都不一样。",
        "tone": "violet",
    },
    {
        "id": "qingxue",
        "voice": "qingxue",
        "raw": "qingxue_bilibili.mp4",
        "show_start_src": 166.35,
        "show": 18.0,
        "crop": "1920:900:0:0",
        "kind": "source",
        "rank": "源头彩蛋",
        "title": "黄莺莺《情雪》",
        "artist": "黄莺莺",
        "tag": "不是同名，但绕不开。",
        "quote": "严格来说它不叫《暧昧》",
        "tone": "paper",
    },
    {
        "id": "hou",
        "voice": "hou",
        "raw": "hou_bilibili.mp4",
        "show_start_src": 198.97,
        "show": 40.5,
        "crop": "1744:1080:0:0",
        "kind": "rank",
        "rank": "第4首",
        "title": "侯湘婷《暧昧》",
        "artist": "侯湘婷",
        "tag": "台湾情歌里的淡淡酸涩",
        "quote": "越平静，越像没走出来。",
        "tone": "warm",
    },
    {
        "id": "xue",
        "voice": "xue",
        "raw": "xue_bilibili.mp4",
        "show_start_src": 142.52,
        "show": 25.2,
        "crop": "1920:880:0:95",
        "kind": "rank",
        "rank": "第3首",
        "title": "薛之谦《暧昧》",
        "artist": "薛之谦",
        "tag": "现代关系里的自我保护",
        "quote": "靠近是真的，退缩也是真的。",
        "tone": "cold",
    },
    {
        "id": "rainie",
        "voice": "rainie",
        "raw": "rainie_bilibili.mp4",
        "show_start_src": 108.09,
        "show": 40.8,
        "crop": "640:480:0:0",
        "kind": "rank",
        "rank": "第2首",
        "title": "杨丞琳《暧昧》",
        "artist": "杨丞琳",
        "tag": "偶像剧时代的全民记忆",
        "quote": "我们到底算什么？",
        "tone": "pink",
    },
    {
        "id": "faye",
        "voice": "faye",
        "raw": "faye_hires_bilibili.mp4",
        "show_start_src": 177.17,
        "show": 56.0,
        "crop": "1620:860:0:160",
        "kind": "rank",
        "rank": "第1首",
        "title": "王菲《暧昧》",
        "artist": "王菲",
        "tag": "近一步越界，退一步不甘心",
        "quote": "不是甜，是发潮。",
        "tone": "wine",
    },
    {
        "id": "outro",
        "voice": "outro",
        "raw": "faye_hires_bilibili.mp4",
        "src_start": 215.99,
        "crop": "1620:860:0:160",
        "show": 0.0,
        "kind": "outro",
        "rank": "",
        "title": "同样叫《暧昧》",
        "artist": "",
        "tag": "每一代人唱的都不一样",
        "quote": "酸涩 / 狼狈 / 委屈 / 克制",
        "tone": "violet",
    },
    {
        "id": "cta",
        "voice": "cta",
        "raw": "faye_hires_bilibili.mp4",
        "src_start": 204.38,
        "crop": "1620:860:0:160",
        "show": 0.0,
        "kind": "cta",
        "rank": "",
        "title": "你最想为哪一首投票？",
        "artist": "",
        "tag": "评论区告诉我",
        "quote": "点赞 / 收藏 / 关注",
        "tone": "violet",
    },
]


def run(cmd: list[str]) -> None:
    print("$", " ".join(shlex.quote(x) for x in cmd), flush=True)
    subprocess.run(cmd, cwd=PROJECT, check=True)


def duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def make_clip(sec: dict, dur: float, src_start: float) -> Path:
    cut = TMP / f"{sec['id']}_cut.mp4"
    out = CLIPS / f"{sec['id']}.mp4"
    raw = RAW / sec["raw"]
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(raw),
            "-ss",
            f"{src_start:.3f}",
            "-t",
            f"{dur:.3f}",
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
            str(cut),
            "-y",
        ]
    )
    run([str(REPO / "tools/video/vfill.sh"), str(cut), str(out), sec["crop"]])
    return out


def make_audio(sec: dict, clip: Path, dur: float) -> Path:
    sid = sec["id"]
    voice = AUDIO / "voice" / f"{sec['voice']}.wav"
    out = AUDIO / "segments" / f"{sid}.wav"
    voice_dur = duration(voice)
    if sid == "intro":
        duck_end = min(dur, voice_dur)
        fc = (
            f"[0:a]loudnorm=I=-20:TP=-2.0:LRA=11,"
            f"atrim=0:{dur:.3f},asetpts=N/SR/TB,"
            f"volume=0.22:enable='between(t,0,{duck_end:.3f})'[m];"
            "[1:a]loudnorm=I=-12:TP=-1.0:LRA=8,volume=1.15,"
            "aresample=48000,aformat=channel_layouts=stereo,apad,"
            f"atrim=0:{dur:.3f},asetpts=N/SR/TB[voice];"
            f"[m][voice]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:{dur:.3f},"
            f"afade=t=out:st={max(0.0, dur - 0.6):.3f}:d=0.6[out]"
        )
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(clip),
                "-i",
                str(voice),
                "-filter_complex",
                fc,
                "-map",
                "[out]",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s16le",
                str(out),
                "-y",
            ]
        )
        return out

    delay_ms = int(LEAD * 1000)
    fade_start = max(0.0, dur - 0.6)
    duck_start = LEAD
    duck_end = min(dur, LEAD + voice_dur)
    fc = (
        f"[0:a]loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{dur:.3f},asetpts=N/SR/TB,"
        f"volume=0.12:enable='between(t,{duck_start:.3f},{duck_end:.3f})'[m];"
        "[1:a]loudnorm=I=-12:TP=-1.0:LRA=8,volume=1.15,"
        f"adelay={delay_ms}:all=1,apad,"
        f"atrim=0:{dur:.3f},asetpts=N/SR/TB[voice];"
        f"[m][voice]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:{dur:.3f},"
        f"afade=t=out:st={fade_start:.3f}:d=0.6[out]"
    )
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(clip),
            "-i",
            str(voice),
            "-filter_complex",
            fc,
            "-map",
            "[out]",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            str(out),
            "-y",
        ]
    )
    return out


def build_html(timeline: list[dict], total: float) -> None:
    timeline_json = json.dumps(timeline, ensure_ascii=False)
    static_nodes: list[str] = []
    for i, s in enumerate(timeline):
        vid_track = 0 if i % 2 == 0 else 6
        overlay_track = 10 if i % 2 == 0 else 11
        classes = f"clip overlay {s['id']} {s['kind']}"
        static_nodes.append(
            f'''      <video id="video-{s['id']}" class="clip bg-video" src="{html_lib.escape(s['clip'])}" muted playsinline data-start="{s['start']:.3f}" data-duration="{s['duration']:.3f}" data-track-index="{vid_track}"></video>'''
        )
        rank = html_lib.escape(s["rank"] or "AIMEI TIMELINE")
        title = html_lib.escape(s["title"])
        tag = html_lib.escape(s["tag"])
        quote = html_lib.escape(s["quote"])
        names = (
            '<div class="names"><span class="pill">王菲</span><span class="pill">杨丞琳</span><span class="pill">薛之谦？</span></div>'
            if s["id"] == "intro"
            else ""
        )
        static_nodes.append(
            f'''      <section id="scene-{s['id']}" class="{classes}" data-start="{s['start']:.3f}" data-duration="{s['duration']:.3f}" data-track-index="{overlay_track}">
        <div>
          <div class="topline"><span class="rank">{rank}</span></div>
          <div class="scene-title">
            <div class="headline">{title}</div>
            <div class="tag">{tag}</div>
            {names}
          </div>
        </div>
        <div class="quote">{quote}</div>
      </section>'''
        )
    for s in timeline[1:]:
        trans_start = max(0.0, s["start"] - 0.34)
        static_nodes.append(
            f'''      <div id="trans-{s['id']}" class="clip transition" data-start="{trans_start:.3f}" data-duration="0.780" data-track-index="50"></div>'''
        )
    static_markup = "\n".join(static_nodes)
    html = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{
        font-family: "Noto Sans SC";
        src: local("PingFang SC"), local("Hiragino Sans GB"), local("STHeiti");
      }}
      @font-face {{
        font-family: "Noto Serif SC";
        src: local("Songti SC"), local("STSong"), local("SimSun");
      }}
      @font-face {{
        font-family: "JetBrains Mono";
        src: local("JetBrains Mono"), local("Menlo"), local("Monaco");
      }}
      * {{ box-sizing: border-box; }}
      html, body {{
        margin: 0;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #08070d;
        color: #d8d0df;
        font-family: "Noto Sans SC", sans-serif;
      }}
      #root {{
        position: relative;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #08070d;
      }}
      .bg-video {{
        position: absolute;
        inset: 0;
        width: 1080px;
        height: 1920px;
        object-fit: cover;
        z-index: 1;
      }}
      .shade {{
        position: absolute;
        inset: 0;
        z-index: 2;
        background:
          radial-gradient(circle at 24% 10%, rgba(127, 92, 255, .28), rgba(127, 92, 255, 0) 34%),
          radial-gradient(circle at 82% 72%, rgba(217, 136, 168, .22), rgba(217, 136, 168, 0) 36%),
          linear-gradient(180deg, rgba(8,7,13,.40), rgba(8,7,13,.22) 45%, rgba(8,7,13,.76));
      }}
      .grain {{
        position: absolute;
        inset: 0;
        z-index: 3;
        opacity: .22;
        background-image:
          linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
        background-size: 34px 34px, 34px 34px;
        mix-blend-mode: soft-light;
      }}
      .overlay {{
        position: absolute;
        inset: 0;
        z-index: 5;
        padding: 132px 78px 118px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        pointer-events: none;
      }}
      .topline {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        font-family: "JetBrains Mono", monospace;
        font-size: 24px;
        letter-spacing: .16em;
        color: rgba(216,208,223,.78);
      }}
      .rank {{
        color: #d988a8;
        font-weight: 800;
      }}
      .scene-title {{
        max-width: 920px;
      }}
      .headline {{
        font-family: "Noto Serif SC", serif;
        font-size: 82px;
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: 0;
        color: #f1e7d6;
        text-shadow: 0 16px 54px rgba(0,0,0,.62);
      }}
      .hook .headline {{
        font-size: 92px;
        max-width: 940px;
      }}
      .tag {{
        margin-top: 24px;
        max-width: 820px;
        font-size: 36px;
        line-height: 1.36;
        font-weight: 650;
        color: #d8d0df;
      }}
      .quote {{
        align-self: flex-start;
        max-width: 860px;
        padding: 28px 34px 30px;
        border-left: 4px solid #7f5cff;
        background: rgba(21,19,34,.60);
        box-shadow: 0 24px 80px rgba(0,0,0,.30);
        backdrop-filter: blur(10px);
        font-family: "Noto Serif SC", serif;
        font-size: 44px;
        line-height: 1.28;
        color: #f1e7d6;
      }}
      .ghost {{
        position: absolute;
        z-index: 4;
        right: -80px;
        bottom: 210px;
        font-family: "Noto Serif SC", serif;
        font-size: 190px;
        font-weight: 800;
        color: rgba(216,208,223,.055);
        writing-mode: vertical-rl;
      }}
      .ghost::before {{
        content: "暧昧";
      }}
      .names {{
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        margin-top: 34px;
      }}
      .pill {{
        padding: 16px 22px;
        border: 1px solid rgba(216,208,223,.28);
        background: rgba(127,92,255,.18);
        border-radius: 999px;
        font-size: 28px;
        color: #f1e7d6;
      }}
      .qingxue .quote {{ border-color: #f1e7d6; }}
      .hou .quote {{ border-color: #d988a8; }}
      .xue .quote {{ border-color: #2f6dff; }}
      .rainie .quote {{ border-color: #d988a8; }}
      .faye .quote {{ border-color: #7b2438; }}
      .transition {{
        position: absolute;
        inset: -180px;
        z-index: 20;
        opacity: 0;
        background:
          radial-gradient(circle at 18% 50%, rgba(241,231,214,.52), rgba(241,231,214,0) 32%),
          radial-gradient(circle at 70% 36%, rgba(127,92,255,.48), rgba(127,92,255,0) 30%),
          linear-gradient(90deg, rgba(123,36,56,.10), rgba(47,109,255,.22), rgba(8,7,13,0));
        filter: blur(26px);
      }}
      .cta .headline {{ font-size: 76px; }}
      .cta .quote {{ font-size: 38px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="1080" data-height="1920">
      <div class="shade"></div>
      <div class="grain"></div>
      <div class="ghost" aria-hidden="true" data-layout-ignore></div>
      <audio id="master-audio" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="60" src="audio/master.wav" data-volume="1"></audio>
{static_markup}
    </div>
    <script>
      const SECTIONS = {timeline_json};

      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      gsap.set("#scene-intro .headline, #scene-intro .tag, #scene-intro .quote, #scene-intro .pill", {{ opacity: 1 }});
      SECTIONS.forEach((s, i) => {{
        const st = s.start;
        const sc = "#scene-" + s.id;
        if (s.id !== "intro") {{
          tl.fromTo(sc + " .topline", {{ opacity: 0, y: -20 }}, {{ opacity: 1, y: 0, duration: .46, ease: "power3.out" }}, st + .14);
          tl.fromTo(sc + " .headline", {{ opacity: 0, y: 54, scale: .98 }}, {{ opacity: 1, y: 0, scale: 1, duration: .72, ease: "expo.out" }}, st + .24);
          tl.fromTo(sc + " .tag", {{ opacity: 0, x: -34 }}, {{ opacity: 1, x: 0, duration: .52, ease: "power2.out" }}, st + .52);
          tl.fromTo(sc + " .quote", {{ opacity: 0, y: 42 }}, {{ opacity: 1, y: 0, duration: .62, ease: "sine.out" }}, st + .78);
        }} else {{
          tl.fromTo(sc + " .pill", {{ opacity: .2, y: 18 }}, {{ opacity: 1, y: 0, stagger: .18, duration: .42, ease: "power2.out" }}, st + 1.2);
        }}
        if (s.show_start !== null) {{
          const t = st + s.full_start - .22;
          tl.to(sc + " .quote", {{ opacity: 0, y: -18, duration: .22, ease: "power2.in" }}, t);
          tl.set(sc + " .quote", {{ opacity: 0, visibility: "hidden" }}, t + .24);
          tl.to(sc + " .topline", {{ opacity: 0, y: -14, duration: .28, ease: "power2.out" }}, t);
          tl.to(sc + " .scene-title", {{ scale: .82, y: -36, opacity: .36, duration: .42, ease: "power2.out" }}, t);
        }}
      }});
      SECTIONS.slice(1).forEach((s) => {{
        const t = s.start - .34;
        tl.to("#trans-" + s.id, {{ opacity: .78, x: 190, duration: .34, ease: "power2.in" }}, t);
        tl.to("#trans-" + s.id, {{ opacity: 0, x: 380, duration: .38, ease: "power2.out" }}, t + .34);
      }});
      tl.to(".ghost", {{ y: -60, duration: {total:.3f}, ease: "none" }}, 0);
      tl.to(".shade", {{ opacity: .86, duration: {total:.3f}, ease: "sine.inOut" }}, 0);
      tl.to("#scene-cta", {{ opacity: 0, duration: 1.1, ease: "power1.in" }}, {max(0, total - 1.2):.3f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    INDEX.write_text(html, encoding="utf-8")


def main() -> None:
    CLIPS.mkdir(parents=True, exist_ok=True)
    (AUDIO / "segments").mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    voice_durs = json.loads((AUDIO / "voice_durations.json").read_text(encoding="utf-8"))
    timeline = []
    audio_files = []
    cursor = 0.0
    for sec in SECTIONS:
        voice_dur = voice_durs[sec["voice"]]
        voice_lead = 0.0 if sec["id"] == "intro" else LEAD
        if sec.get("show_start_src") is not None:
            full_start = LEAD + voice_dur + POST
            dur = full_start + sec["show"]
            src_start = max(0.0, sec["show_start_src"] - full_start)
            show_start_abs = cursor + full_start
        else:
            full_start = None
            dur = LEAD + voice_dur + 1.3
            src_start = sec["src_start"]
            show_start_abs = None
        clip = make_clip(sec, dur, src_start)
        audio = make_audio(sec, clip, dur)
        audio_files.append(audio)
        timeline.append(
            {
                **{k: sec[k] for k in ["id", "kind", "rank", "title", "artist", "tag", "quote", "tone"]},
                "start": round(cursor, 3),
                "duration": round(dur, 3),
                "voice_start": round(cursor + voice_lead, 3),
                "voice_end": round(cursor + voice_lead + voice_dur, 3),
                "full_start": round(full_start, 3) if full_start is not None else None,
                "show_start": round(show_start_abs, 3) if show_start_abs is not None else None,
                "show": round(sec["show"], 3),
                "src_start": round(src_start, 3),
                "src_show_start": sec.get("show_start_src"),
                "clip": f"clips/{sec['id']}.mp4",
                "crop": sec["crop"],
            }
        )
        cursor += dur

    concat = TMP / "audio_concat.txt"
    concat.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in audio_files) + "\n",
        encoding="utf-8",
    )
    master_tmp = AUDIO / "master_pre.wav"
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(master_tmp),
            "-y",
        ]
    )
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(master_tmp),
            "-af",
            "loudnorm=I=-14:TP=-1.0:LRA=11",
            str(AUDIO / "master.wav"),
            "-y",
        ]
    )

    total = round(cursor, 3)
    TIMELINE.write_text(
        json.dumps({"total_duration": total, "sections": timeline}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    build_html(timeline, total)
    print(TIMELINE)
    print(INDEX)
    print(AUDIO / "master.wav")


if __name__ == "__main__":
    main()
