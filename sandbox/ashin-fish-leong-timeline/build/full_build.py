#!/usr/bin/env python3
"""构建《原来阿信把另一种五月天，写进了梁静茹的歌里》。

产物：
- master.wav：预混音频，最终必须 mux 覆盖 HyperFrames 音轨。
- hf/clips_seg/*.mp4：每首最终使用窗口，已竖屏 letterbox 并去掉可裁水印/歌词。
- hf/index.html：HyperFrames 竖屏 composition。
"""
import contextlib
import json
import shutil
import subprocess
import wave
from pathlib import Path


ROOT = Path(".")
RAW = ROOT / "raw"
AUDIO = ROOT / "audio"
ASSETS = ROOT / "assets"
HF = ROOT / "hf"
SEG = ROOT / "build" / "segs"


def dur_wav(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def fmt(x):
    return f"{round(float(x), 3)}"


SONGS = [
    {
        "key": "rainbow",
        "no": "01",
        "year": "1999",
        "title": "彩虹",
        "album": "一夜长大",
        "credit": "作曲：阿信｜作词：阿信、梁伯君",
        "tag": "抱不住的爱",
        "keyword": "潮湿",
        "raw": "rainbow_bili.mp4",
        "crop": "1920:760:0:130",
        "onset": 219.34,
        "show": 58.0,
        "bg": "#0B1114",
        "accent": "#75B8D8",
        "accent2": "#E7CFA4",
        "motif": "雨后彩虹",
    },
    {
        "key": "beautiful",
        "no": "02",
        "year": "2003",
        "title": "Beautiful",
        "album": "美丽人生",
        "credit": "作词：阿信｜作曲：蔡健雅",
        "tag": "开始看见自己",
        "keyword": "漂亮",
        "raw": "beautiful_bili.mp4",
        "crop": "1920:760:0:130",
        "onset": 120.51,
        "show": 52.0,
        "bg": "#142017",
        "accent": "#DDE8BE",
        "accent2": "#F0B7C8",
        "motif": "镜面反光",
    },
    {
        "key": "cant_hear",
        "no": "03",
        "year": "2003",
        "title": "听不到",
        "album": "恋爱的力量",
        "credit": "词曲：阿信",
        "tag": "说不出口的委屈",
        "keyword": "失语",
        "raw": "cant_hear_bili.mp4",
        "crop": "1920:820:0:100",
        "onset": 135.67,
        "show": 52.0,
        "bg": "#101820",
        "accent": "#9DB7D5",
        "accent2": "#F1D8A0",
        "motif": "静音波形",
    },
    {
        "key": "swallowtail",
        "no": "04",
        "year": "2004",
        "title": "燕尾蝶",
        "album": "燕尾蝶 下定爱的决心",
        "credit": "词曲：阿信",
        "tag": "为爱破蛹",
        "keyword": "破蛹",
        "raw": "swallowtail_bili.mp4",
        "crop": "1920:560:0:220",
        "onset": 149.77,
        "show": 55.0,
        "bg": "#1E0D08",
        "accent": "#E56F37",
        "accent2": "#F6D09B",
        "motif": "火光和翅膀",
    },
    {
        "key": "innocence",
        "no": "05",
        "year": "2004",
        "title": "纯真",
        "album": "燕尾蝶 下定爱的决心",
        "credit": "词曲：阿信｜五月天旧作再演绎",
        "tag": "回头看见失去",
        "keyword": "回望",
        "raw": "innocence_bili.mp4",
        "crop": "926:440:0:110",
        "onset": 248.85,
        "show": 58.0,
        "bg": "#17140F",
        "accent": "#E1C48B",
        "accent2": "#DCE6F0",
        "motif": "旧照片",
    },
    {
        "key": "silkroad",
        "no": "06",
        "year": "2005",
        "title": "丝路",
        "album": "丝路 通往爱的路途",
        "credit": "作词：阿信｜作曲、制作：王力宏",
        "tag": "把爱唱成远行",
        "keyword": "远行",
        "raw": "silkroad_bili.mp4",
        "crop": "1920:740:0:150",
        "onset": 123.69,
        "show": 60.0,
        "bg": "#21140A",
        "accent": "#D9A64E",
        "accent2": "#F3E1B0",
        "motif": "地图路线",
    },
    {
        "key": "coke_ring",
        "no": "07",
        "year": "2006",
        "title": "可乐戒指",
        "album": "亲亲",
        "credit": "作词：阿信｜作曲：Jasemaine",
        "tag": "把承诺落回日常",
        "keyword": "承诺",
        "raw": "coke_ring_bili_alt1.mp4",
        "crop": "1920:780:0:150",
        "onset": 72.03,
        "show": 50.0,
        "bg": "#101D18",
        "accent": "#BFE7D0",
        "accent2": "#E8B66A",
        "motif": "可乐拉环",
    },
]

for idx, song in enumerate(SONGS, start=1):
    song["voice_key"] = f"s{idx}_voice"

LEAD = 0.15
PRE_VOICE = 0.80
POST_VOICE = 1.20
SWELL = 1.50
BED = 0.20
BED_FLOOR = 0.08
TAIL = 1.20


def voice_duration(key):
    return dur_wav(AUDIO / f"{key}.wav")


NARR = {"intro": voice_duration("intro"), "outro": voice_duration("outro"), "cta": voice_duration("cta")}
for song in SONGS:
    NARR[song["voice_key"]] = voice_duration(song["voice_key"])


def song_anchors(song):
    voice = NARR[song["voice_key"]]
    voice_at = LEAD + PRE_VOICE
    voice_end = voice_at + voice
    sw0 = voice_end + POST_VOICE
    full0 = sw0 + SWELL
    full1 = full0 + song["show"]
    end = full1 + TAIL
    mseek = max(0.0, song["onset"] - (voice_end - 2.0))
    return {
        "voice_at": voice_at,
        "voice_end": voice_end,
        "sw0": sw0,
        "full0": full0,
        "full1": full1,
        "end": end,
        "mseek": round(mseek, 3),
    }


INTRO_D = max(20.0, LEAD + NARR["intro"] + 4.0)
OUTRO_VOICE_AT = LEAD + 0.45
CTA_AT = OUTRO_VOICE_AT + NARR["outro"] + 1.05
OUTRO_D = CTA_AT + NARR["cta"] + 2.2

starts = {}
t = 0.0
starts["intro"] = (t, INTRO_D)
t += INTRO_D
for song in SONGS:
    a = song_anchors(song)
    starts[song["key"]] = (t, a["end"])
    t += a["end"]
starts["outro"] = (t, OUTRO_D)
t += OUTRO_D
TOTAL = round(t, 3)

print("NARR", json.dumps(NARR, ensure_ascii=False, indent=2))
print("TOTAL", TOTAL)

SEG.mkdir(parents=True, exist_ok=True)


def music_volume_expr(voice_at, sw0, full0):
    return (
        f"(lt(t,{voice_at}))*({BED_FLOOR}+({BED - BED_FLOOR})*t/{voice_at})"
        f"+(between(t,{voice_at},{sw0}))*{BED}"
        f"+(between(t,{sw0},{full0}))*({BED}+{1.0 - BED}*(t-{sw0})/{SWELL})"
        f"+(gte(t,{full0}))*1.0"
    )


def build_intro():
    # 用《可乐戒指》现场低音量铺底，让片头不死静。
    out = SEG / "seg_intro.wav"
    run([
        "ffmpeg",
        "-v",
        "error",
        "-i",
        RAW / "coke_ring_bili_alt1.mp4",
        "-i",
        AUDIO / "intro.wav",
        "-filter_complex",
        (
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={int((LEAD + 0.2) * 1000)}|{int((LEAD + 0.2) * 1000)},volume=2.0[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
            f"atrim=58:{58 + INTRO_D},asetpts=PTS-STARTPTS,volume=0.16,"
            f"afade=t=in:st=0:d=1.0,afade=t=out:st={INTRO_D - 1.4}:d=1.4[bed];"
            f"[bed][voice]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_D},alimiter=limit=0.95[out]"
        ),
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        out,
        "-y",
    ])
    return out


def build_song_audio(song):
    key = song["key"]
    a = song_anchors(song)
    seg_len = a["end"]
    voice_at = a["voice_at"]
    sw0 = a["sw0"]
    full0 = a["full0"]
    full1 = a["full1"]
    ve = music_volume_expr(voice_at, sw0, full0)
    out = SEG / f"seg_{key}.wav"
    run([
        "ffmpeg",
        "-v",
        "error",
        "-i",
        RAW / song["raw"],
        "-i",
        AUDIO / f"{song['voice_key']}.wav",
        "-filter_complex",
        (
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={int(voice_at * 1000)}|{int(voice_at * 1000)},volume=2.0[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
            f"atrim={a['mseek']}:{a['mseek'] + seg_len},asetpts=PTS-STARTPTS,"
            f"volume='{ve}':eval=frame,afade=t=out:st={full1}:d={TAIL}[music];"
            f"[music][voice]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.95[out]"
        ),
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        out,
        "-y",
    ])
    return out


def build_outro():
    out = SEG / "seg_outro.wav"
    run([
        "ffmpeg",
        "-v",
        "error",
        "-i",
        RAW / "rainbow_bili.mp4",
        "-i",
        AUDIO / "outro.wav",
        "-i",
        AUDIO / "cta.wav",
        "-filter_complex",
        (
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={int(OUTRO_VOICE_AT * 1000)}|{int(OUTRO_VOICE_AT * 1000)},volume=2.0[outrovo];"
            f"[2:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={int(CTA_AT * 1000)}|{int(CTA_AT * 1000)},volume=2.0[ctavo];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
            f"atrim=219:{219 + OUTRO_D},asetpts=PTS-STARTPTS,volume=0.18,"
            f"afade=t=in:st=0:d=1.0,afade=t=out:st={OUTRO_D - 1.8}:d=1.8[bed];"
            f"[bed][outrovo][ctavo]amix=inputs=3:normalize=0:duration=longest,atrim=0:{OUTRO_D},alimiter=limit=0.95[out]"
        ),
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        out,
        "-y",
    ])
    return out


seg_paths = [build_intro()]
for s in SONGS:
    seg_paths.append(build_song_audio(s))
seg_paths.append(build_outro())

seglist = SEG / "seglist.txt"
seglist.write_text("".join(f"file '{p.name}'\n" for p in seg_paths), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", seglist, "-ac", "2", "-ar", "48000", "master.wav", "-y"])

HF.mkdir(exist_ok=True)
(HF / "clips_seg").mkdir(parents=True, exist_ok=True)
(HF / "fonts").mkdir(parents=True, exist_ok=True)
(HF / "vendor").mkdir(parents=True, exist_ok=True)
(HF / "assets").mkdir(parents=True, exist_ok=True)

for name in ["ashin_portrait.jpg", "fish_portrait.jpg"]:
    src = ASSETS / name
    if not src.exists():
        raise FileNotFoundError(f"missing cover portrait: {src}")
    shutil.copy(src, HF / "assets" / name)

for src, dst in [
    (Path("/System/Library/Fonts/Supplemental/Songti.ttc"), HF / "fonts" / "Songti.ttc"),
    (Path("/System/Library/Fonts/STHeiti Medium.ttc"), HF / "fonts" / "STHeiti-Medium.ttc"),
    (Path("/System/Library/Fonts/Menlo.ttc"), HF / "fonts" / "Menlo.ttc"),
]:
    if src.exists() and not dst.exists():
        shutil.copy(src, dst)

gsap_dst = HF / "vendor" / "gsap.min.js"
if not gsap_dst.exists():
    for candidate in ROOT.parent.glob("*/vendor/gsap.min.js"):
        shutil.copy(candidate, gsap_dst)
        break

shutil.copy("master.wav", HF / "master.wav")
(HF / "package.json").write_text(
    json.dumps(
        {
            "name": "ashin-fish-leong-timeline",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "npx --yes hyperframes@0.6.47 preview",
                "check": "npx --yes hyperframes@0.6.47 lint && npx --yes hyperframes@0.6.47 validate && npx --yes hyperframes@0.6.47 inspect",
                "render": "npx --yes hyperframes@0.6.47 render",
            },
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
(HF / "hyperframes.json").write_text('{"version":"0.6.47"}\n', encoding="utf-8")
(HF / "meta.json").write_text(json.dumps({"id": "main", "name": "ashin-fish-leong-timeline"}, ensure_ascii=False), encoding="utf-8")


def build_video_clip(song):
    a = song_anchors(song)
    out = HF / "clips_seg" / f"{song['key']}.mp4"
    br = "-0.28"
    sat = "1.08"
    run([
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        a["mseek"],
        "-i",
        RAW / song["raw"],
        "-t",
        a["end"],
        "-filter_complex",
        (
            f"[0:v]crop={song['crop']},split=2[bg][fg];"
            f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"gblur=sigma=30,eq=brightness={br}:saturation={sat}[bgb];"
            f"[fg]scale=1080:-2[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
        ),
        "-map",
        "[v]",
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
        "-an",
        out,
        "-y",
    ])
    return out


for song in SONGS:
    build_video_clip(song)


abs_song = {}
for song in SONGS:
    st, d = starts[song["key"]]
    a = song_anchors(song)
    abs_song[song["key"]] = {
        "start": st,
        "end": st + d,
        "voice_at": st + a["voice_at"],
        "sw0": st + a["sw0"],
        "full0": st + a["full0"],
        "full1": st + a["full1"],
    }

intro_start, intro_d = starts["intro"]
outro_start, outro_d = starts["outro"]

video_tags = []
for idx, song in enumerate(SONGS):
    st, d = starts[song["key"]]
    video_tags.append(
        f'<video id="video_{song["key"]}" class="clip footage" data-start="{fmt(st)}" '
        f'data-duration="{fmt(d)}" data-track-index="{idx % 2}" src="clips_seg/{song["key"]}.mp4" muted playsinline></video>'
    )

song_cards = []
for idx, song in enumerate(SONGS):
    st, d = starts[song["key"]]
    song_cards.append(
        f'''<section id="card_{song["key"]}" class="clip song-card" data-start="{fmt(st)}" data-duration="{fmt(d)}" data-track-index="{20 + idx}" style="--bg:{song["bg"]};--accent:{song["accent"]};--accent2:{song["accent2"]}">
  <div class="side-rail"><span>{song["no"]}</span></div>
  <div class="info-card">
    <div class="meta"><span>{song["year"]}</span><span>{song["album"]}</span></div>
    <h2>{song["title"]}</h2>
    <p class="credit">{song["credit"]}</p>
    <p class="tag">{song["tag"]}</p>
  </div>
  <div class="keyword">{song["keyword"]}</div>
  <div class="motif">{song["motif"]}</div>
</section>'''
    )

intro_keywords = ["雨后", "镜面", "电话", "蝴蝶", "旧照", "长路", "拉环"]
intro_html = f'''<section id="intro" class="clip intro" data-start="0" data-duration="{fmt(INTRO_D)}" data-track-index="40">
  <div class="vinyl" data-layout-allow-overflow></div>
  <div class="cover-left"><img src="assets/ashin_portrait.jpg" alt=""><span>Mayday's other timeline</span></div>
  <div class="cover-right"><img src="assets/fish_portrait.jpg" alt=""><span>Fish Leong's love songs</span></div>
  <h1>阿信写给梁静茹的<br>另一条青春线</h1>
  <p class="intro-sub">不是歌单罗列，是一条从青春到成熟的情绪路径</p>
  <div class="motif-grid">{''.join(f'<b>{k}</b>' for k in intro_keywords)}</div>
  <div class="listen-title">按时间顺序听一遍</div>
</section>'''

outro_html = f'''<section id="outro" class="clip outro" data-start="{fmt(outro_start)}" data-duration="{fmt(outro_d)}" data-track-index="41">
  <div class="bubble-field"></div>
  <h2>彩虹 / 漂亮 / 失语 / 破蛹 / 纯真 / 远行 / 承诺</h2>
  <p class="outro-copy">阿信留下的是支线，梁静茹唱成了自己的成长史。</p>
  <div class="cta-card">评论区投票</div>
</section>'''

audio_tag = f'<audio id="master_audio" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="90" src="master.wav" data-volume="1"></audio>'

CSS = r'''
@font-face { font-family: "SongtiLocal"; src: url("fonts/Songti.ttc") format("truetype-collection"); font-weight: 400 900; font-style: normal; }
@font-face { font-family: "HeitiLocal"; src: url("fonts/STHeiti-Medium.ttc") format("truetype-collection"); font-weight: 400 900; font-style: normal; }
@font-face { font-family: "MonoLocal"; src: url("fonts/Menlo.ttc") format("truetype-collection"); font-weight: 400 900; font-style: normal; }
* { box-sizing: border-box; }
html, body { margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #06070b; color: #f7efe2; font-family: "SongtiLocal", serif; }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #06070b; }
.footage { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; opacity: 0; z-index: 1; }
.song-card { position: absolute; inset: 0; z-index: 5; pointer-events: none; overflow: hidden; }
.song-card::before { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.10), rgba(0,0,0,.38) 54%, rgba(0,0,0,.72)); z-index: -1; }
.song-card::after { content: ""; position: absolute; inset: -20%; background: radial-gradient(circle at 18% 22%, color-mix(in srgb, var(--accent) 28%, transparent), transparent 34%), radial-gradient(circle at 85% 72%, color-mix(in srgb, var(--accent2) 18%, transparent), transparent 30%); opacity: .75; z-index: -1; }
.side-rail { position: absolute; left: 76px; top: 132px; bottom: 170px; width: 4px; background: linear-gradient(180deg, transparent, rgba(255,255,255,.34), transparent); opacity: 0; }
.side-rail span { position: absolute; top: 0; left: -24px; width: 52px; height: 52px; border-radius: 999px; display: grid; place-items: center; color: #fff8ea; background: rgba(6,7,11,.82); border: 2px solid var(--accent); font: 800 22px/1 "HeitiLocal", sans-serif; }
.info-card { position: absolute; top: 122px; right: 56px; width: 670px; padding: 44px 46px 42px; border: 1.5px solid rgba(255,255,255,.20); border-radius: 24px; background: linear-gradient(135deg, rgba(10,10,14,.70), rgba(10,10,14,.38)); backdrop-filter: blur(28px); box-shadow: 0 26px 80px rgba(0,0,0,.48); opacity: 0; }
.meta { display: flex; gap: 18px; align-items: center; font: 800 24px/1.2 "HeitiLocal", sans-serif; letter-spacing: .18em; color: var(--accent); margin-bottom: 22px; }
.meta span + span { color: rgba(247,239,226,.62); letter-spacing: .08em; }
.info-card h2 { margin: 0 0 20px; font-size: 86px; line-height: 1.02; letter-spacing: 0; font-weight: 900; color: #fff8ea; }
.credit { margin: 0 0 22px; font: 500 28px/1.45 "HeitiLocal", sans-serif; color: rgba(255,255,255,.78); }
.tag { margin: 0; display: inline-block; padding: 12px 18px; border-radius: 999px; background: color-mix(in srgb, var(--accent) 18%, transparent); color: #fff9ea; font: 800 30px/1.2 "HeitiLocal", sans-serif; }
.keyword { position: absolute; left: 0; right: 0; bottom: 292px; text-align: center; font-size: 180px; line-height: .92; font-weight: 900; color: var(--accent); opacity: 0; text-shadow: 0 0 52px color-mix(in srgb, var(--accent) 45%, transparent); }
.motif { position: absolute; left: 76px; bottom: 150px; font: 800 30px/1 "HeitiLocal", sans-serif; letter-spacing: .28em; color: rgba(255,255,255,.62); opacity: 0; }
.intro { position: absolute; inset: 0; z-index: 20; background: radial-gradient(circle at 20% 24%, rgba(72,111,160,.42), transparent 28%), radial-gradient(circle at 84% 60%, rgba(229,111,55,.22), transparent 34%), linear-gradient(180deg, #07101b, #080709 70%); overflow: hidden; }
.intro::after { content: ""; position: absolute; inset: 0; background-image: radial-gradient(circle at 10% 20%, rgba(255,255,255,.08) 0 1px, transparent 1.3px), radial-gradient(circle at 70% 60%, rgba(255,255,255,.07) 0 1px, transparent 1.4px); background-size: 150px 160px, 210px 190px; opacity: .58; }
.vinyl { position: absolute; width: 760px; height: 760px; border-radius: 50%; right: -250px; top: 120px; background: repeating-radial-gradient(circle, rgba(255,255,255,.13) 0 2px, rgba(255,255,255,.02) 2px 8px), radial-gradient(circle, #111 0 16%, #08080b 17% 100%); opacity: .72; }
.cover-left, .cover-right { position: absolute; top: 160px; width: 420px; height: 560px; border: 1.5px solid rgba(255,255,255,.18); border-radius: 24px; overflow: hidden; display: flex; align-items: end; padding: 30px; font: 800 22px/1.2 "MonoLocal", monospace; letter-spacing: .08em; color: rgba(255,255,255,.78); text-transform: uppercase; box-shadow: 0 30px 80px rgba(0,0,0,.42); }
.cover-left { left: 70px; background: linear-gradient(145deg, rgba(41,96,170,.50), rgba(8,10,16,.72)); }
.cover-right { right: 70px; background: linear-gradient(145deg, rgba(218,151,75,.42), rgba(8,10,16,.74)); }
.cover-left::after, .cover-right::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(4,6,10,.02) 0%, rgba(4,6,10,.20) 48%, rgba(4,6,10,.76) 100%); }
.cover-left img, .cover-right img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: saturate(.92) contrast(1.06); }
.cover-left img { object-position: 50% 38%; }
.cover-right img { object-position: 50% 28%; }
.cover-left span, .cover-right span { position: relative; z-index: 2; text-shadow: 0 2px 16px rgba(0,0,0,.70); }
.intro h1 { position: absolute; left: 72px; right: 72px; top: 790px; margin: 0; font-size: 112px; line-height: 1.08; font-weight: 900; letter-spacing: 0; z-index: 2; }
.intro-sub { position: absolute; left: 76px; right: 76px; top: 1070px; margin: 0; font: 600 34px/1.5 "HeitiLocal", sans-serif; color: rgba(255,255,255,.72); z-index: 2; }
.motif-grid { position: absolute; left: 76px; right: 76px; bottom: 238px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; z-index: 2; }
.motif-grid b { padding: 18px 10px; text-align: center; border: 1.5px solid rgba(255,255,255,.18); border-radius: 16px; background: rgba(255,255,255,.06); font: 800 30px/1 "HeitiLocal", sans-serif; color: rgba(255,255,255,.76); opacity: 0; }
.listen-title { position: absolute; left: 76px; right: 76px; bottom: 132px; padding: 22px 0 10px; border-top: 2px solid rgba(255,255,255,.24); font: 900 38px/1.2 "HeitiLocal", sans-serif; letter-spacing: .12em; color: #f2d08a; opacity: 0; z-index: 2; }
.outro { position: absolute; inset: 0; z-index: 19; background: radial-gradient(circle at 50% 40%, rgba(191,231,208,.18), transparent 34%), linear-gradient(180deg, #08120f, #070708); overflow: hidden; opacity: 0; }
.bubble-field { position: absolute; inset: 0; background-image: radial-gradient(circle at 15% 88%, rgba(191,231,208,.24) 0 9px, transparent 10px), radial-gradient(circle at 35% 78%, rgba(232,182,106,.18) 0 6px, transparent 7px), radial-gradient(circle at 70% 86%, rgba(191,231,208,.20) 0 12px, transparent 13px); }
.outro h2 { position: absolute; left: 72px; right: 72px; top: 430px; font-size: 66px; line-height: 1.6; margin: 0; color: #fff7e8; opacity: 0; }
.outro-copy { position: absolute; left: 76px; right: 76px; top: 980px; margin: 0; font: 600 44px/1.5 "HeitiLocal", sans-serif; color: rgba(255,255,255,.74); opacity: 0; }
.cta-card { position: absolute; left: 76px; right: 76px; bottom: 300px; padding: 34px 40px; border-radius: 24px; background: rgba(191,231,208,.14); border: 1.5px solid rgba(191,231,208,.35); font: 900 44px/1.2 "HeitiLocal", sans-serif; color: #bfe7d0; text-align: center; opacity: 0; }
'''

js_lines = [
    "window.__timelines = window.__timelines || {};",
    "const tl = gsap.timeline({ paused: true });",
    "tl.set('#intro', { opacity: 1 }, 0);",
    "tl.fromTo('.cover-left', { opacity: 0, x: -50, rotation: -2 }, { opacity: 1, x: 0, rotation: -2, duration: .7, ease: 'power3.out' }, .2);",
    "tl.fromTo('.cover-right', { opacity: 0, x: 50, rotation: 2 }, { opacity: 1, x: 0, rotation: 2, duration: .7, ease: 'power3.out' }, .35);",
    "tl.fromTo('.intro h1', { opacity: 0, y: 46 }, { opacity: 1, y: 0, duration: .9, ease: 'expo.out' }, .8);",
    "tl.fromTo('.intro-sub', { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: .7, ease: 'power2.out' }, 1.7);",
    "tl.to('.vinyl', { rotation: 18, scale: 1.04, duration: 18, ease: 'none' }, 0);",
    "tl.fromTo('.motif-grid b', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: .35, stagger: .18, ease: 'power2.out' }, 4.6);",
    "tl.fromTo('.listen-title', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .6, ease: 'power2.out' }, 8.0);",
    f"tl.to('#intro', {{ opacity: 0, duration: .8, ease: 'power2.in' }}, {fmt(INTRO_D - .8)});",
    f"tl.set('#intro', {{ opacity: 0 }}, {fmt(INTRO_D)});",
]

for song in SONGS:
    key = song["key"]
    a = abs_song[key]
    st = a["start"]
    end = a["end"]
    full0 = a["full0"]
    full1 = a["full1"]
    js_lines.extend([
        f"tl.fromTo('#video_{key}', {{ opacity: 0, scale: 1.045 }}, {{ opacity: 1, scale: 1.0, duration: 1.2, ease: 'power2.out' }}, {fmt(st)});",
        f"tl.fromTo('#card_{key} .side-rail', {{ opacity: 0 }}, {{ opacity: 1, duration: .65, ease: 'power1.out' }}, {fmt(st + .25)});",
        f"tl.fromTo('#card_{key} .info-card', {{ opacity: 0, x: 54, y: -18 }}, {{ opacity: 1, x: 0, y: 0, duration: .8, ease: 'power3.out' }}, {fmt(st + .55)});",
        f"tl.fromTo('#card_{key} .motif', {{ opacity: 0, x: -24 }}, {{ opacity: .85, x: 0, duration: .55, ease: 'power2.out' }}, {fmt(st + 1.05)});",
        f"tl.to('#card_{key} .info-card', {{ opacity: 0, y: -12, duration: .5, ease: 'power2.in' }}, {fmt(a['sw0'] - .1)});",
        f"tl.fromTo('#card_{key} .keyword', {{ opacity: 0, scale: .9 }}, {{ opacity: .48, scale: 1, duration: 1.1, ease: 'power3.out' }}, {fmt(full0 - .35)});",
        f"tl.to('#card_{key} .keyword', {{ opacity: .58, duration: 1.0, ease: 'sine.inOut' }}, {fmt(full0 + 1.0)});",
        f"tl.to('#card_{key} .keyword', {{ opacity: 0, duration: .9, ease: 'power1.in' }}, {fmt(full1 - 1.0)});",
        f"tl.to('#video_{key}', {{ opacity: 0, duration: .85, ease: 'power1.in' }}, {fmt(end - .85)});",
        f"tl.set('#video_{key}', {{ opacity: 0 }}, {fmt(end)});",
        f"tl.to('#card_{key} .side-rail, #card_{key} .motif', {{ opacity: 0, duration: .55, ease: 'power1.in' }}, {fmt(end - .65)});",
    ])

js_lines.extend([
    f"tl.fromTo('#outro', {{ opacity: 0 }}, {{ opacity: 1, duration: .8, ease: 'power2.out' }}, {fmt(outro_start)});",
    f"tl.fromTo('.outro h2', {{ opacity: 0, y: 34 }}, {{ opacity: 1, y: 0, duration: .9, ease: 'power3.out' }}, {fmt(outro_start + .45)});",
    f"tl.fromTo('.outro-copy', {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: .75, ease: 'power2.out' }}, {fmt(outro_start + 3.0)});",
    f"tl.fromTo('.cta-card', {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: .6, ease: 'power2.out' }}, {fmt(outro_start + CTA_AT - .2)});",
    f"tl.to('#outro', {{ opacity: 0, duration: 1.2, ease: 'power1.in' }}, {fmt(TOTAL - 1.2)});",
    f"tl.set('#outro', {{ opacity: 0 }}, {fmt(TOTAL)});",
    "window.__timelines['main'] = tl;",
])

html = f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1920">
  <script src="vendor/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
    {chr(10).join(video_tags)}
    {chr(10).join(song_cards)}
    {intro_html}
    {outro_html}
    {audio_tag}
  </div>
  <script>
    {chr(10).join(js_lines)}
  </script>
</body>
</html>'''

(HF / "index.html").write_text(html, encoding="utf-8")


def composition_html(body, js, duration, base_href=""):
    base_tag = f'\n  <base href="{base_href}">' if base_href else ""
    return f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1920">{base_tag}
  <script src="vendor/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(duration)}" data-width="1080" data-height="1920">
    {body}
  </div>
  <script>
    {chr(10).join(js)}
  </script>
</body>
</html>'''


def write_part(name, body, js, duration):
    part_dir = HF / "parts_html"
    part_dir.mkdir(parents=True, exist_ok=True)
    path = part_dir / f"{name}.html"
    path.write_text(composition_html(body, js, duration, "../"), encoding="utf-8")
    return path


intro_part_js = [
    "window.__timelines = window.__timelines || {};",
    "const tl = gsap.timeline({ paused: true });",
    "tl.set('#intro', { opacity: 1 }, 0);",
    "tl.fromTo('.cover-left', { opacity: 0, x: -50, rotation: -2 }, { opacity: 1, x: 0, rotation: -2, duration: .7, ease: 'power3.out' }, .2);",
    "tl.fromTo('.cover-right', { opacity: 0, x: 50, rotation: 2 }, { opacity: 1, x: 0, rotation: 2, duration: .7, ease: 'power3.out' }, .35);",
    "tl.fromTo('.intro h1', { opacity: 0, y: 46 }, { opacity: 1, y: 0, duration: .9, ease: 'expo.out' }, .8);",
    "tl.fromTo('.intro-sub', { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: .7, ease: 'power2.out' }, 1.7);",
    "tl.to('.vinyl', { rotation: 18, scale: 1.04, duration: 18, ease: 'none' }, 0);",
    "tl.fromTo('.motif-grid b', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: .35, stagger: .18, ease: 'power2.out' }, 4.6);",
    "tl.fromTo('.listen-title', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .6, ease: 'power2.out' }, 8.0);",
    f"tl.to('#intro', {{ opacity: 0, duration: .8, ease: 'power2.in' }}, {fmt(INTRO_D - .8)});",
    f"tl.set('#intro', {{ opacity: 0 }}, {fmt(INTRO_D)});",
    "window.__timelines['main'] = tl;",
]
part_paths = [write_part("part_00_intro", intro_html, intro_part_js, INTRO_D)]

for idx, song in enumerate(SONGS, start=1):
    key = song["key"]
    a = song_anchors(song)
    d = a["end"]
    local_video = (
        f'<video id="video_{key}" class="clip footage" data-start="0" '
        f'data-duration="{fmt(d)}" data-track-index="0" src="clips_seg/{key}.mp4" muted playsinline></video>'
    )
    local_card = f'''<section id="card_{key}" class="clip song-card" data-start="0" data-duration="{fmt(d)}" data-track-index="20" style="--bg:{song["bg"]};--accent:{song["accent"]};--accent2:{song["accent2"]}">
  <div class="side-rail"><span>{song["no"]}</span></div>
  <div class="info-card">
    <div class="meta"><span>{song["year"]}</span><span>{song["album"]}</span></div>
    <h2>{song["title"]}</h2>
    <p class="credit">{song["credit"]}</p>
    <p class="tag">{song["tag"]}</p>
  </div>
  <div class="keyword">{song["keyword"]}</div>
  <div class="motif">{song["motif"]}</div>
</section>'''
    song_part_js = [
        "window.__timelines = window.__timelines || {};",
        "const tl = gsap.timeline({ paused: true });",
        f"tl.fromTo('#video_{key}', {{ opacity: 0, scale: 1.045 }}, {{ opacity: 1, scale: 1.0, duration: 1.2, ease: 'power2.out' }}, 0);",
        f"tl.fromTo('#card_{key} .side-rail', {{ opacity: 0 }}, {{ opacity: 1, duration: .65, ease: 'power1.out' }}, .25);",
        f"tl.fromTo('#card_{key} .info-card', {{ opacity: 0, x: 54, y: -18 }}, {{ opacity: 1, x: 0, y: 0, duration: .8, ease: 'power3.out' }}, .55);",
        f"tl.fromTo('#card_{key} .motif', {{ opacity: 0, x: -24 }}, {{ opacity: .85, x: 0, duration: .55, ease: 'power2.out' }}, 1.05);",
        f"tl.to('#card_{key} .info-card', {{ opacity: 0, y: -12, duration: .5, ease: 'power2.in' }}, {fmt(a['sw0'] - .1)});",
        f"tl.fromTo('#card_{key} .keyword', {{ opacity: 0, scale: .9 }}, {{ opacity: .48, scale: 1, duration: 1.1, ease: 'power3.out' }}, {fmt(a['full0'] - .35)});",
        f"tl.to('#card_{key} .keyword', {{ opacity: .58, duration: 1.0, ease: 'sine.inOut' }}, {fmt(a['full0'] + 1.0)});",
        f"tl.to('#card_{key} .keyword', {{ opacity: 0, duration: .9, ease: 'power1.in' }}, {fmt(a['full1'] - 1.0)});",
        f"tl.to('#video_{key}', {{ opacity: 0, duration: .85, ease: 'power1.in' }}, {fmt(d - .85)});",
        f"tl.set('#video_{key}', {{ opacity: 0 }}, {fmt(d)});",
        f"tl.to('#card_{key} .side-rail, #card_{key} .motif', {{ opacity: 0, duration: .55, ease: 'power1.in' }}, {fmt(d - .65)});",
        "window.__timelines['main'] = tl;",
    ]
    part_paths.append(write_part(f"part_{idx:02d}_{key}", f"{local_video}\n{local_card}", song_part_js, d))

outro_part_html = f'''<section id="outro" class="clip outro" data-start="0" data-duration="{fmt(OUTRO_D)}" data-track-index="41">
  <div class="bubble-field"></div>
  <h2>彩虹 / 漂亮 / 失语 / 破蛹 / 纯真 / 远行 / 承诺</h2>
  <p class="outro-copy">阿信留下的是支线，梁静茹唱成了自己的成长史。</p>
  <div class="cta-card">评论区投票</div>
</section>'''
outro_part_js = [
    "window.__timelines = window.__timelines || {};",
    "const tl = gsap.timeline({ paused: true });",
    "tl.fromTo('#outro', { opacity: 0 }, { opacity: 1, duration: .8, ease: 'power2.out' }, 0);",
    "tl.fromTo('.outro h2', { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: .9, ease: 'power3.out' }, .45);",
    "tl.fromTo('.outro-copy', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: .75, ease: 'power2.out' }, 3.0);",
    f"tl.fromTo('.cta-card', {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: .6, ease: 'power2.out' }}, {fmt(CTA_AT - .2)});",
    f"tl.to('#outro', {{ opacity: 0, duration: 1.2, ease: 'power1.in' }}, {fmt(OUTRO_D - 1.2)});",
    f"tl.set('#outro', {{ opacity: 0 }}, {fmt(OUTRO_D)});",
    "window.__timelines['main'] = tl;",
]
part_paths.append(write_part("part_08_outro", outro_part_html, outro_part_js, OUTRO_D))

build_meta = {
    "total": TOTAL,
    "starts": starts,
    "songs": [
        {
            **{k: song[k] for k in ["key", "title", "year", "album", "credit", "raw", "crop", "onset", "show"]},
            "mseek": song_anchors(song)["mseek"],
            "section_start": starts[song["key"]][0],
            "section_duration": starts[song["key"]][1],
            "full_start_abs": abs_song[song["key"]]["full0"],
            "full_end_abs": abs_song[song["key"]]["full1"],
        }
        for song in SONGS
    ],
    "outro": {"start": outro_start, "duration": OUTRO_D, "cta_at": outro_start + CTA_AT},
}
(ROOT / "build_meta.json").write_text(json.dumps(build_meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("WROTE", HF / "index.html", "TOTAL", TOTAL)
