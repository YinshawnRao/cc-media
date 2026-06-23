#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import shlex
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
AUDIO = PROJECT / "audio"
CLIPS = PROJECT / "clips"
RENDERS = PROJECT / "renders"
TTS = REPO / "tools" / "tts" / "venv" / "bin" / "python"
NARRATE = REPO / "tools" / "tts" / "narrate.py"


SONGS = [
    {
        "key": "xiju",
        "rank": "TOP 5",
        "title": "喜剧收场",
        "clip": "clips/xiju_bridge.mp4",
        "source_start": 150,
        "source_end": 213,
        "range": "克制铺陈 → 再次拥抱我",
        "pre": "第五名，《喜剧收场》。先听这段转折。",
        "critique": "所谓喜剧收场，其实是哭着谢幕。",
        "post": "所谓喜剧收场，其实是哭着谢幕。它不是把痛唱满，而是把体面一点点拆掉，最后还想再次拥抱。",
    },
    {
        "key": "yangwang",
        "rank": "TOP 4",
        "title": "仰望",
        "clip": "clips/yangwang_bridge.mp4",
        "source_start": 157,
        "source_end": 187.8,
        "range": "无法预知 → 守候后的空白",
        "pre": "第四名，《仰望》。这一段不是甜，是撑。",
        "critique": "前面是等待，这里是硬撑。",
        "post": "前面是等待，这里是硬撑。她把不确定唱得很轻，但轻到最后，反而像一直没说出口的求救。",
    },
    {
        "key": "daiwozou",
        "rank": "TOP 3",
        "title": "带我走",
        "clip": "clips/daiwozou_bridge.mp4",
        "source_start": 150,
        "source_end": 168.0,
        "range": "柔光回望 → 带我走之前",
        "pre": "第三名，《带我走》。这一段从柔光里，把逃离唱成求救。",
        "critique": "听起来像奔赴，其实像求救。",
        "post": "听起来像奔赴，其实像求救。它不是要一个目的地，而是要一个人，把她从原地带走。",
    },
    {
        "key": "niming",
        "rank": "TOP 2",
        "title": "匿名的好友",
        "clip": "clips/niming_bridge.mp4",
        "source_start": 53,
        "source_end": 70,
        "range": "也许我们当时年纪真的太小 → 但思念还转动",
        "pre": "第二名，《匿名的好友》。这段才是全歌真正的伤口。",
        "critique": "副歌是结果，这段才是病根。",
        "post": "副歌是结果，这段才是病根。年纪太小，名字太轻，所以后来每一次想起，都像不敢承认的后遗症。",
    },
    {
        "key": "left",
        "rank": "TOP 1",
        "title": "左边",
        "clip": "clips/left_bridge.mp4",
        "source_start": 92,
        "source_end": 126,
        "range": "我一直相信总有一天 → 你说的那句我爱你",
        "pre": "第一名，《左边》。不用爆发，它已经够痛。",
        "critique": "不是爆发，是忍住崩溃。",
        "post": "不是爆发，是忍住崩溃。她把我爱你唱到几乎落地，却还是没有真正等到一个确定答案。",
    },
]


NARRATION = {
    "intro": "有些歌真正高级的地方，不一定在副歌。而是在副歌之后，那一小段突然转弯的 bridge。杨丞琳这五段 bridge，都是情绪突然变深的瞬间。",
    "outro": "这五段 bridge，厉害的地方不只是高音或转调，而是它们都在副歌之后，突然把故事往更痛的地方推了一步。",
    "cta": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。",
}


def run(cmd: list[str]) -> None:
    print("+", " ".join(shlex.quote(str(x)) for x in cmd))
    subprocess.run([str(x) for x in cmd], check=True)


def capture(cmd: list[str]) -> str:
    return subprocess.check_output([str(x) for x in cmd], text=True).strip()


def duration(path: Path) -> float:
    out = capture([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
    ])
    return float(out)


def ensure_tts() -> dict[str, Path]:
    AUDIO.mkdir(parents=True, exist_ok=True)
    texts: dict[str, str] = {
        "intro": NARRATION["intro"],
        "outro": NARRATION["outro"],
        "cta": NARRATION["cta"],
    }
    for song in SONGS:
        texts[f"{song['key']}_pre"] = song["pre"]

    paths: dict[str, Path] = {}
    for key, text in texts.items():
        txt = AUDIO / f"{key}.txt"
        wav = AUDIO / f"{key}.wav"
        desired = text + "\n"
        previous = txt.read_text(encoding="utf-8") if txt.exists() else None
        txt.write_text(desired, encoding="utf-8")
        paths[key] = wav
        if previous == desired and wav.exists() and wav.stat().st_size > 1024:
            continue
        run([TTS, NARRATE, txt, "--female", "--speed", "1.04", "-o", wav])
    return paths


def make_voice_segment(name: str, voice: Path, bed_clip: Path, dur: float) -> Path:
    out = AUDIO / f"seg_{name}.wav"
    dur = round(dur, 3)
    run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-stream_loop",
        "-1",
        "-i",
        bed_clip,
        "-i",
        voice,
        "-filter_complex",
        (
            f"[0:a]atrim=0:{dur},asetpts=PTS-STARTPTS,volume=0.10,"
            "loudnorm=I=-30:TP=-5:LRA=7,aresample=48000,"
            "aformat=sample_rates=48000:channel_layouts=stereo[bed];"
            f"[1:a]adelay=120|120,apad,atrim=0:{dur},asetpts=PTS-STARTPTS,"
            "volume=1.0,aresample=48000,"
            "aformat=sample_rates=48000:channel_layouts=stereo[vo];"
            "[bed][vo]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
            "loudnorm=I=-18:TP=-1.5:LRA=9[out]"
        ),
        "-map",
        "[out]",
        "-c:a",
        "pcm_s16le",
        "-ar",
        "48000",
        out,
        "-y",
    ])
    return out


def make_bridge_segment(song: dict[str, object], dur: float) -> Path:
    clip = PROJECT / str(song["clip"])
    out = AUDIO / f"seg_{song['key']}_bridge.wav"
    fade_start = max(0.0, dur - 0.45)
    run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        clip,
        "-vn",
        "-af",
        (
            "loudnorm=I=-14:TP=-1.0:LRA=11,"
            "afade=t=in:st=0:d=0.25,"
            f"afade=t=out:st={fade_start:.3f}:d=0.45,"
            "aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo"
        ),
        "-c:a",
        "pcm_s16le",
        "-ar",
        "48000",
        out,
        "-y",
    ])
    return out


def build_audio_and_timeline() -> tuple[list[dict[str, object]], float]:
    voice = ensure_tts()
    events: list[dict[str, object]] = []
    audio_parts: list[Path] = []
    t = 0.0
    track = 10

    def add_scene(kind: str, duration_s: float, audio: Path | None = None, **extra: object) -> None:
        nonlocal t, track
        ev = {"kind": kind, "start": round(t, 3), "duration": round(duration_s, 3), "track": track}
        ev.update(extra)
        events.append(ev)
        if audio is not None:
            audio_parts.append(audio)
        t += duration_s
        track += 1

    first_clip = PROJECT / SONGS[0]["clip"]
    intro_d = max(8.0, duration(voice["intro"]) + 1.2)
    add_scene(
        "intro",
        intro_d,
        make_voice_segment("intro", voice["intro"], first_clip, intro_d),
        title="杨丞琳最超神的5段Bridge",
        subtitle="盘的不是副歌，是情绪突然转弯的那一段",
    )

    for i, song in enumerate(SONGS):
        key = str(song["key"])
        clip = PROJECT / str(song["clip"])
        clip_d = duration(clip)
        card_d = max(3.2, duration(voice[f"{key}_pre"]) + 0.8)
        add_scene(
            "card",
            card_d,
            make_voice_segment(f"{key}_pre", voice[f"{key}_pre"], clip, card_d),
            rank=song["rank"],
            title=song["title"],
            range=song["range"],
            song_key=key,
        )
        add_scene(
            "bridge",
            clip_d,
            make_bridge_segment(song, clip_d),
            rank=song["rank"],
            title=song["title"],
            range=song["range"],
            clip=song["clip"],
            song_key=key,
            video_track=0 if i % 2 == 0 else 6,
        )

    outro_d = max(6.0, duration(voice["outro"]) + 1.0)
    add_scene(
        "outro",
        outro_d,
        make_voice_segment("outro", voice["outro"], PROJECT / SONGS[-1]["clip"], outro_d),
        title="Bridge 不只是过门",
        subtitle="它是故事真正拐弯的地方",
    )
    cta_d = max(8.5, duration(voice["cta"]) + 1.8)
    add_scene(
        "cta",
        cta_d,
        make_voice_segment("cta", voice["cta"], PROJECT / SONGS[-1]["clip"], cta_d),
        title="你最想为哪一首投票？",
        subtitle="评论区告诉我",
    )

    concat = AUDIO / "segments.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in audio_parts), encoding="utf-8")
    master = PROJECT / "master.wav"
    run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat,
        "-c:a",
        "pcm_s16le",
        "-ar",
        "48000",
        master,
        "-y",
    ])
    return events, round(t, 3)


def attrs(**items: object) -> str:
    return " ".join(f'{k.replace("_", "-")}="{html.escape(str(v), quote=True)}"' for k, v in items.items())


def scene_div(ev: dict[str, object], body: str, classes: str = "") -> str:
    allow = " data-layout-allow-occlusion" if "bridge-overlay" in classes else ""
    return (
        f'<section class="clip scene {classes}" '
        f'{attrs(id=f"scene-{ev["track"]}", data_start=ev["start"], data_duration=ev["duration"], data_track_index=ev["track"])}{allow}>'
        f"{body}</section>"
    )


def build_html(events: list[dict[str, object]], total: float) -> None:
    pieces: list[str] = []
    pieces.append(
        f'<audio id="master-audio" class="clip" src="master.wav" '
        f'{attrs(data_start=0, data_duration=total, data_track_index=98)}></audio>'
    )

    for ev in events:
        kind = ev["kind"]
        start = ev["start"]
        dur = ev["duration"]
        if kind == "intro":
            cover_clip = html.escape(SONGS[0]["clip"], quote=True)
            pieces.append(
                f'<video id="cover-video" class="clip cover-video" src="{cover_clip}" muted playsinline '
                f'{attrs(data_start=start, data_duration=dur, data_track_index=70)}></video>'
            )
            pieces.append(scene_div(ev, f"""
              <div class="cover-title-wrap">
                <p class="cover-pretitle">懂歌的人，听这一小段转弯</p>
                <h1>
                  <span>杨丞琳最超神的</span>
                  <span>5段Bridge</span>
                </h1>
              </div>
              <div class="cover-bottom-copy">
                <p>盘的不是副歌</p>
                <p>是情绪突然变深的那一段</p>
              </div>
            """, "intro-scene"))
        elif kind == "card":
            pieces.append(scene_div(ev, f"""
              <div class="card-safe">
                <div class="rank">{html.escape(str(ev["rank"]))}</div>
                <h2>《{html.escape(str(ev["title"]))}》</h2>
                <p class="range">{html.escape(str(ev["range"]))}</p>
                <div class="thin-line"></div>
              </div>
            """, f"card-scene tone-{ev['song_key']}"))
        elif kind == "bridge":
            clip = html.escape(str(ev["clip"]), quote=True)
            pieces.append(
                f'<video id="video-{ev["song_key"]}" class="clip bridge-video" src="{clip}" muted playsinline '
                f'{attrs(data_start=start, data_duration=dur, data_track_index=ev["video_track"])}></video>'
            )
            pieces.append(scene_div(ev, f"""
              <div class="bridge-range">{html.escape(str(ev["range"]))}</div>
            """, "bridge-overlay"))
        elif kind == "outro":
            pieces.append(scene_div(ev, f"""
              <h2>{html.escape(str(ev["title"]))}</h2>
              <p>{html.escape(str(ev["subtitle"]))}</p>
            """, "outro-scene"))
        elif kind == "cta":
            pieces.append(scene_div(ev, f"""
              <h2>{html.escape(str(ev["title"]))}</h2>
              <p>{html.escape(str(ev["subtitle"]))}</p>
              <div class="cta-actions">
                <span>点赞</span><span>收藏</span><span>关注</span>
              </div>
            """, "cta-scene"))

    css = """
      :root { color-scheme: dark; }
      * { box-sizing: border-box; }
      body { margin: 0; overflow: hidden; background: #08080a; font-family: sans-serif; }
      #rainie-bridge-top5 { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #08080a; color: #f4f0e8; }
      #rainie-bridge-top5::before {
        content: ""; position: absolute; inset: 0; z-index: 1; pointer-events: none;
        background:
          linear-gradient(180deg, rgba(0,0,0,.56), rgba(0,0,0,0) 24%, rgba(0,0,0,0) 68%, rgba(0,0,0,.58)),
          repeating-linear-gradient(0deg, rgba(255,255,255,.024) 0, rgba(255,255,255,.024) 1px, transparent 1px, transparent 4px);
        mix-blend-mode: screen; opacity: .42;
      }
      .bridge-video, .cover-video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0; background: #050505; }
      .cover-video { filter: contrast(1.08) saturate(1.08) brightness(.72); transform: scale(1.035); }
      .scene { position: absolute; inset: 0; z-index: 5; width: 100%; height: 100%; padding: 150px 104px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 28px; background: radial-gradient(circle at 50% 32%, rgba(185, 166, 128, .12), transparent 38%), #08080a; }
      .scene::after { content: ""; position: absolute; inset: 74px; border: 1px solid rgba(232, 217, 184, .18); pointer-events: none; }
      .intro-scene {
        z-index: 7;
        align-items: center;
        text-align: center;
        justify-content: space-between;
        padding: 154px 96px 178px;
        background:
          radial-gradient(circle at 50% 18%, rgba(246, 219, 156, .22), rgba(246, 219, 156, 0) 32%),
          linear-gradient(180deg, rgba(0,0,0,.72), rgba(0,0,0,.22) 28%, rgba(0,0,0,.08) 54%, rgba(0,0,0,.72));
      }
      .intro-scene::after { inset: 96px; border-color: rgba(244, 220, 169, .26); }
      .cover-title-wrap { width: 100%; max-width: 880px; display: flex; flex-direction: column; align-items: center; gap: 20px; margin: 0 auto; text-align: center; }
      .cover-pretitle { margin: 0; color: rgba(244,240,232,.82); font-size: 32px; line-height: 1.32; }
      h1 { margin: 0; font-size: 94px; line-height: 1.08; letter-spacing: 0; font-weight: 900; max-width: 880px; text-wrap: balance; text-shadow: 0 14px 38px rgba(0,0,0,.72); }
      .cover-title-wrap h1 { display: flex; flex-direction: column; align-items: center; gap: 6px; width: 100%; max-width: 860px; font-size: 90px; line-height: 1.04; text-align: center; }
      .cover-title-wrap h1 span { display: block; width: 100%; text-align: center; }
      .cover-title-wrap h1 span:first-child { font-size: 78px; }
      .cover-title-wrap h1 span:last-child { font-size: 98px; color: #fffaf0; }
      h2 { margin: 0; font-size: 82px; line-height: 1.1; letter-spacing: 0; font-weight: 850; max-width: 820px; text-wrap: balance; }
      .question { color: #f0c975; font-size: 42px; font-weight: 800; margin-top: 4px; }
      .cover-bottom-copy { width: 100%; max-width: 820px; display: flex; flex-direction: column; align-items: center; gap: 12px; margin: 0 auto; color: rgba(244,240,232,.88); text-align: center; text-shadow: 0 12px 30px rgba(0,0,0,.72); }
      .cover-bottom-copy p { margin: 0; font-size: 43px; line-height: 1.22; font-weight: 760; }
      .cover-bottom-copy p:first-child { color: #f0c975; font-size: 35px; font-weight: 700; }
      .card-safe { width: 100%; max-width: 820px; min-height: 560px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 28px; padding: 52px 56px; background: rgba(0,0,0,.24); border: 1px solid rgba(232,217,184,.16); }
      .rank { color: #c7a15b; font-family: ui-serif, Georgia, serif; font-size: 60px; line-height: 1; font-weight: 700; }
      .rank.small { font-size: 38px; }
      .range { margin: 0; color: rgba(244,240,232,.72); font-size: 35px; line-height: 1.36; max-width: 760px; text-wrap: balance; }
      .thin-line { width: 180px; height: 2px; background: #c7a15b; opacity: .76; margin-top: 12px; }
      .card-scene { background: linear-gradient(180deg, #0c0b0d, #111014); }
      .bridge-overlay { z-index: 6; justify-content: flex-end; background: transparent; padding: 92px 86px 118px; pointer-events: none; }
      .bridge-overlay::after { display: none; }
      .bridge-range { align-self: center; width: min(820px, 100%); padding: 24px 30px; background: rgba(0,0,0,.50); border-left: 4px solid #c7a15b; color: rgba(244,240,232,.90); font-size: 33px; line-height: 1.34; text-align: center; backdrop-filter: blur(16px); }
      blockquote { margin: 28px 0 0; padding: 10px 0 12px 34px; border-left: 5px solid #c7a15b; font-size: 52px; line-height: 1.34; font-weight: 800; max-width: 850px; color: #f4f0e8; }
      .outro-scene, .cta-scene { text-align: center; align-items: center; background: linear-gradient(180deg, #09090b, #141114); }
      .outro-scene p, .cta-scene p { margin: 0; max-width: 790px; color: rgba(244,240,232,.72); font-size: 42px; line-height: 1.4; }
      .cta-actions { display: flex; gap: 16px; margin-top: 30px; }
      .cta-actions span { min-width: 126px; padding: 15px 24px; border: 1px solid rgba(199,161,91,.48); color: #c7a15b; font-size: 30px; }
    """

    js = f"""
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.to({{}}, {{ duration: {total:.3f} }}, 0);
      window.__timelines["rainie-bridge-top5"] = tl;
    """

    html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Rainie Bridge Top 5</title>
</head>
<body>
  <main id="rainie-bridge-top5" data-composition-id="rainie-bridge-top5" data-start="0" data-duration="{total:.3f}" data-width="1080" data-height="1920">
    {''.join(pieces)}
  </main>
  <style>{css}</style>
  <script src="vendor/gsap.min.js"></script>
  <script>{js}</script>
</body>
</html>
"""
    (PROJECT / "index.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    events, total = build_audio_and_timeline()
    build_html(events, total)
    (PROJECT / "timeline.json").write_text(json.dumps({"duration": total, "events": events}, ensure_ascii=False, indent=2), encoding="utf-8")
    (PROJECT / "narration.json").write_text(json.dumps({"intro": NARRATION["intro"], "songs": SONGS, "outro": NARRATION["outro"], "cta": NARRATION["cta"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"duration={total:.3f}s")
    print(PROJECT / "index.html")
    print(PROJECT / "master.wav")


if __name__ == "__main__":
    main()
