#!/usr/bin/env python3
"""张韶涵前7张专辑·冷门遗珠盘点 — v2 build。
关键变更（用户反馈）：
1. 严禁文字重叠（全局排版手算 collision-safe）。
2. 首屏封面 = 大小标题 + 7 张专辑「真人封面拼贴」（每图含张韶涵），t=0 静态可截屏。
3. 删除 hook flash 段（"垃圾时间"）。
4. 开头第一段配音不被截断（intro_d ≥ voice_at + voice_dur + buffer）。
5. 配音开始时才显示 7 首歌单列表（动画淡入）。
6. 每首歌转场 = footage + UI 同时出现；专辑卡新格式（歌名大字 / 专辑名·年份 / 描述），低透明度，无《》。
7. 结尾简化，删去歌单列表（开头已显示），文案精简。
"""
import json
import shutil
import subprocess
import wave
import contextlib
from pathlib import Path

A = "audio"; C = "clips"; HF = "hf"

def dur(p):
    with contextlib.closing(wave.open(str(p), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

NARR = json.loads(Path("narration.json").read_text(encoding="utf-8"))
NARR_DUR = {k: v["dur"] for k, v in NARR.items()}

SONGS = [
    dict(key="s1", no="01", year="2004", song="天边", album="Over The Rainbow",
         desc="想长大，想离开，想自己决定方向"),
    dict(key="s2", no="02", year="2004", song="浮云", album="欧若拉",
         desc="梦幻、漂浮，被同名主打盖住的那一首"),
    dict(key="s3", no="03", year="2006", song="保护色", album="潘朵拉",
         desc="防备、带刺，前半段第一个节奏提神点"),
    dict(key="s4", no="04", year="2007", song="寻宝", album="梦里花",
         desc="童话宇宙的支线，继续寻找的勇气"),
    dict(key="s5", no="05", year="2007", song="能不能勇敢说爱", album="Ang 5.0",
         desc="青春直球，偶像剧感，被大热盖住"),
    dict(key="s6", no="06", year="2009", song="偶尔", album="第5季",
         desc="全片情绪核心，遗憾、回头、轻失落"),
    dict(key="s7", no="07", year="2012", song="是我", album="有形的翅膀",
         desc="自我确认，前面都在飞，走到这里回到自己"),
]
KEYS = [s["key"] for s in SONGS]
KEY2NUM = {f"s{i+1}": f"{i+1:02d}" for i in range(7)}
def clip_path(key): return f"{C}/vert_{KEY2NUM[key]}.mp4"

# ============ 节奏常量 ============
COVER_HOLD = 2.5    # 封面静止时长（截图用）
COVER_BUFFER = 1.3  # 封面退场缓冲（与 s1 接续）
LEAD = 0.18         # 段首预滚
PRE_VOICE = 0.35    # voice 起前的音乐床起伏
POST_VOICE = 1.10   # voice 收尾消化位
SWELL = 1.20        # 床→full swell
FADE = 1.0          # 段尾淡出
BED_GAIN = 0.28     # voice 期音乐床增益
ALBUM_CARD_DUR = 3.0  # 专辑卡在 footage 上覆盖时长（淡入 + 持续 + 淡出）

OUTRO_CTA = 11.0    # 互动 CTA（简化无列表）

def song_seg(key):
    voice_d = NARR_DUR[f"{key}_voice"]
    mid_d = NARR_DUR[f"{key}_mid"]
    high_d = 21.0  # 副歌展示
    trans_d = max(mid_d + 0.5, 3.5)
    return LEAD + PRE_VOICE + voice_d + POST_VOICE + SWELL + high_d + trans_d + FADE

# 累计时间表
starts = {}
intro_voice_d = NARR_DUR["intro"]
INTRO_D = COVER_HOLD + intro_voice_d + COVER_BUFFER  # 例：2.5 + 9.2 + 1.3 = 13.0s
t = 0.0
starts["intro"] = (t, INTRO_D); t += INTRO_D
for k in KEYS:
    d = song_seg(k); starts[k] = (t, d); t += d
starts["outro"] = (t, OUTRO_CTA); t += OUTRO_CTA
TOTAL = round(t, 3)
print(f"TOTAL: {TOTAL}s = {int(TOTAL)//60}:{TOTAL%60:05.2f}")
for k, (a, b) in starts.items():
    print(f"  {k:7s} {a:8.3f} - {a+b:8.3f}  ({b:6.2f}s)")

def anchors(key):
    voice_d = NARR_DUR[f"{key}_voice"]
    mid_d = NARR_DUR[f"{key}_mid"]
    high_d = 21.0
    trans_d = max(mid_d + 0.5, 3.5)
    a = {}
    a["v0"] = LEAD + PRE_VOICE
    a["v1"] = a["v0"] + voice_d
    a["sw0"] = a["v1"] + POST_VOICE
    a["full0"] = a["sw0"] + SWELL
    a["full1"] = a["full0"] + high_d
    a["trans0"] = a["full1"]
    a["trans1"] = a["full1"] + trans_d
    a["end"] = a["trans1"] + FADE
    return a

def fmt(x): return f"{round(x, 3)}"

# ============ 音频构建 ============
SEG = Path("build/segs"); SEG.mkdir(parents=True, exist_ok=True)

# Intro 段：cover_hold 静音乐床起步 + voice + 缓冲
intro_d = INTRO_D
intro_voice_at = COVER_HOLD  # 封面静止后立即开始旁白
run(["ffmpeg","-v","error","-i", clip_path("s7"), "-i", f"{A}/intro.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(intro_voice_at*1000)}|{int(intro_voice_at*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=20:{20+intro_d},asetpts=PTS-STARTPTS,volume=0.22,"
     f"afade=t=in:st=0:d=1.2,afade=t=out:st={intro_d-1.3}:d=1.3[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_d},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_intro.wav","-y"])
print(f"seg_intro built ({intro_d}s; voice_at={intro_voice_at})")

# 每首歌：footage 与 album_card 同时入场，music 床全程不断
def build_song(s):
    k = s["key"]
    a = anchors(k)
    seg_len = starts[k][1]
    voice_at = a["v0"]
    mid_at = a["trans0"] + 0.3
    sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]
    trans0 = a["trans0"]; trans1 = a["trans1"]; end = a["end"]
    # 床/swell 包络（无 0 段）
    ve = (
        f"(lt(t,{LEAD}))*({BED_GAIN}*t/{LEAD})"
        f"+(between(t,{LEAD},{sw0}))*{BED_GAIN}"
        f"+(between(t,{sw0},{full0}))*({BED_GAIN}+{1.0-BED_GAIN}*(t-{sw0})/{SWELL})"
        f"+(between(t,{full0},{full1}))*1.0"
        f"+(between(t,{full1},{trans1}))*(1.0-(1.0-{BED_GAIN})*(t-{full1})/{max(trans1-full1,0.01)})"
        f"+(gte(t,{trans1}))*({BED_GAIN}*(1-(t-{trans1})/{max(end-trans1,0.01)}))"
    )
    extra_gain = 3.5 if k in ("s6", "s7") else 0.0
    music_src = clip_path(k)
    music_take = seg_len + 1.0
    music_filter = (
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{music_take},asetpts=PTS-STARTPTS,"
        f"volume={1.0 if extra_gain==0 else round(10**(extra_gain/20),3)},"
        f"volume='{ve}':eval=frame[music];"
    )
    voice_filter = (
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[voice];"
    )
    mid_filter = (
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"adelay={int(mid_at*1000)}|{int(mid_at*1000)},volume=2.0[mid];"
    )
    mix = "[music][voice][mid]amix=inputs=3:normalize=0:duration=longest,atrim=0:" + str(seg_len) + ",alimiter=limit=0.95[out]"
    out = f"build/segs/seg_{k}.wav"
    run(["ffmpeg","-v","error",
         "-i", music_src,
         "-i", f"{A}/{k}_voice.wav",
         "-i", f"{A}/{k}_mid.wav",
         "-filter_complex", music_filter + voice_filter + mid_filter + mix,
         "-map","[out]","-ac","2","-ar","48000", out, "-y"])
    print(f"seg_{k} built ({seg_len:.2f}s)")

for s in SONGS: build_song(s)

# Outro 段
outro_d = starts["outro"][1]
outro_voice_at = LEAD
run(["ffmpeg","-v","error","-i", clip_path("s7"), "-i", f"{A}/outro.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(outro_voice_at*1000)}|{int(outro_voice_at*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=30:{30+outro_d},asetpts=PTS-STARTPTS,volume=0.24,"
     f"afade=t=in:st=0:d=1.0,afade=t=out:st={outro_d-2.0}:d=2.0[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_d},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])
print(f"seg_outro built ({outro_d}s)")

# 拼 master.wav
seg_files = ["seg_intro.wav"] + [f"seg_{k}.wav" for k in KEYS] + ["seg_outro.wav"]
(SEG / "seglist.txt").write_text("".join(f"file '{f}'\n" for f in seg_files), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i", str(SEG / "seglist.txt"),
     "-ac","2","-ar","48000","master.wav","-y"])
print(f"master.wav built (planned {TOTAL}s)")

# ============ 预切 clips_seg/ ============
# 每首歌 footage 现在与段同长（与 album_card 同时入场，无前置 dark 期）
Path(f"{HF}/clips_seg").mkdir(parents=True, exist_ok=True)
for s in SONGS:
    k = s["key"]
    video_dur = starts[k][1]
    src = clip_path(k)
    dest = f"{HF}/clips_seg/{k}.mp4"
    run(["ffmpeg","-v","error","-i", src, "-t", str(video_dur),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
         "-pix_fmt","yuv420p","-an", dest, "-y"])
shutil.copy("master.wav", f"{HF}/master.wav")

# 绝对锚点
abs_ = {}
for s in SONGS:
    k = s["key"]
    base = starts[k][0]
    a = anchors(k)
    abs_[k] = {kk: round(base + vv, 3) for kk, vv in a.items()}
    abs_[k]["seg_start"] = round(base, 3)
    abs_[k]["seg_end"] = round(base + starts[k][1], 3)

# ============ HTML 构建 ============

# 通用 CSS — 整理排版位置以避免碰撞
CSS = '''
:root {
  --night-blue: #10182F; --night-deep: #060A1C;
  --mist-purple: #7C6AAE; --ice-blue: #9DD6F9;
  --silver-white: #F4F7FB; --warm-cream: #FFF1D6;
  --rose-dark: #B96A82; --film-gray: #7E8494;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden;
  background: var(--night-deep);
  font-family: "PingFang SC","HarmonyOS Sans SC","Noto Sans SC","Source Han Sans SC", system-ui, sans-serif;
  color: var(--silver-white); -webkit-font-smoothing: antialiased; }
h1, h2, h3, p { margin: 0; padding: 0; }

/* footage 全屏，1 层 */
.fv { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 1; opacity: 0; }
/* scrim 让 UI 文字可读 */
.scrim { position: absolute; inset: 0; z-index: 2;
  background: linear-gradient(180deg, rgba(6,10,28,0.32) 0%, rgba(6,10,28,0.10) 30%, rgba(6,10,28,0.10) 70%, rgba(6,10,28,0.72) 100%);
  pointer-events: none; opacity: 0; }
.grain { position: absolute; inset: 0; z-index: 3; pointer-events: none; opacity: .09;
  background-image: radial-gradient(rgba(255,255,255,0.18) 0.6px, transparent 0.6px);
  background-size: 5px 5px; mix-blend-mode: overlay; }

/* 右上角角标（无《》） */
.corner { position: absolute; top: 70px; right: 50px; max-width: 800px; padding: 14px 22px;
  border-radius: 22px; font-size: 32px; line-height: 1.2; font-weight: 600; text-align: right;
  color: rgba(244,247,251,0.96); background: rgba(16,24,47,0.50);
  border: 1px solid rgba(244,247,251,0.20); backdrop-filter: blur(14px); z-index: 20; opacity: 0; }
.corner .pri { color: var(--silver-white); font-weight: 800; letter-spacing: .02em; }
.corner .sep { color: rgba(244,247,251,0.50); margin: 0 10px; font-weight: 500; }
.corner .alb { color: rgba(244,247,251,0.78); font-weight: 500; }

/* 新版专辑卡（与 footage 同时入场，低透明度，无《》） */
.albumcard {
  position: absolute; left: 56px; right: 56px; bottom: 180px;
  padding: 36px 40px; border-radius: 30px;
  background: linear-gradient(135deg, rgba(16,24,47,0.42), rgba(124,106,174,0.18)), rgba(16,24,47,0.32);
  border: 1px solid rgba(244,247,251,0.18);
  box-shadow: 0 24px 70px rgba(0,0,0,0.40);
  backdrop-filter: blur(18px); z-index: 22; opacity: 0;
}
.albumcard-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.albumcard-index { font-size: 28px; letter-spacing: .16em; color: rgba(244,247,251,0.78);
  font-family: "Inter","Avenir Next","Helvetica Neue", system-ui, sans-serif; font-weight: 700; }
.albumcard-tag { padding: 9px 16px; border-radius: 999px; font-size: 24px; font-weight: 800;
  color: var(--night-blue);
  background: linear-gradient(135deg, var(--ice-blue), var(--warm-cream)); }
.albumcard-song { font-size: 96px; line-height: 1.05; font-weight: 800;
  letter-spacing: -.02em; color: var(--silver-white);
  text-shadow: 0 6px 24px rgba(0,0,0,0.45); margin-bottom: 16px; }
.albumcard-album { font-size: 34px; line-height: 1.3; font-weight: 500;
  color: rgba(255,241,214,0.92); letter-spacing: .04em; margin-bottom: 14px; }
.albumcard-album .year { color: rgba(244,247,251,0.65); margin-left: 14px; font-family: "Inter", system-ui, sans-serif; font-weight: 600; }
.albumcard-desc { font-size: 28px; line-height: 1.4; color: rgba(244,247,251,0.78); font-weight: 400; }

/* 副歌段字幕 */
.caption { position: absolute; left: 64px; right: 64px; bottom: 110px;
  padding: 24px 32px; border-radius: 24px; font-size: 40px; line-height: 1.42;
  font-weight: 600; color: #fff; background: rgba(16,24,47,0.58);
  text-shadow: 0 3px 12px rgba(0,0,0,0.46); backdrop-filter: blur(14px);
  z-index: 23; opacity: 0; text-align: center; }

/* 首屏封面 */
.cover { position: absolute; inset: 0; z-index: 56;
  background: radial-gradient(ellipse at 50% 28%, #1A2447 0%, #10182F 60%, #060A1C 100%); overflow: hidden; }
.cover-grain { position: absolute; inset: 0; pointer-events: none; opacity: .11;
  background-image: radial-gradient(rgba(244,247,251,.30) 0.7px, transparent 0.8px);
  background-size: 5px 5px; mix-blend-mode: overlay; }
.cover-eyebrow {
  position: absolute; top: 92px; left: 0; right: 0; text-align: center;
  font-size: 24px; letter-spacing: .42em; font-weight: 700; color: rgba(157,214,249,0.88);
  font-family: "Inter","Avenir Next","Helvetica Neue", system-ui, sans-serif;
}
.cover-title {
  position: absolute; top: 160px; left: 60px; right: 60px; text-align: center;
  font-size: 116px; line-height: 1.06; font-weight: 900; letter-spacing: -.03em;
  color: var(--silver-white); text-shadow: 0 10px 36px rgba(0,0,0,.55);
}
.cover-sub {
  position: absolute; top: 470px; left: 0; right: 0; text-align: center;
  font-size: 36px; font-weight: 500; color: var(--warm-cream); letter-spacing: .06em;
}
/* 7 张 face thumb 拼贴：4+3 居中 */
.cover-grid {
  position: absolute; top: 540px; left: 60px; right: 60px; height: 590px;
}
.cv-row { display: flex; justify-content: center; gap: 16px; }
.cv-row1 { margin-bottom: 18px; }
.cv-cell { width: 226px; height: 268px; border-radius: 18px; overflow: hidden;
  background-size: cover; background-position: center;
  box-shadow: 0 16px 40px rgba(0,0,0,0.55), inset 0 0 0 1.5px rgba(244,247,251,0.20);
}
.cv-cell .nb { position: absolute; top: 10px; left: 10px;
  padding: 5px 12px; font-size: 18px; font-weight: 800;
  letter-spacing: .12em; color: var(--night-blue);
  background: rgba(244,247,251,0.92); border-radius: 8px;
  font-family: "Inter", sans-serif; }
.cv-cell { position: relative; }
/* 7 face image hooks */
.cv-c1 { background-image: url("cover_assets/face_01.jpg"); }
.cv-c2 { background-image: url("cover_assets/face_02.jpg"); }
.cv-c3 { background-image: url("cover_assets/face_03.jpg"); }
.cv-c4 { background-image: url("cover_assets/face_04.jpg"); }
.cv-c5 { background-image: url("cover_assets/face_05.jpg"); }
.cv-c6 { background-image: url("cover_assets/face_06.jpg"); }
.cv-c7 { background-image: url("cover_assets/face_07.jpg"); }

/* 列表（旁白起时淡入） */
.cover-list {
  position: absolute; top: 1170px; left: 96px; right: 96px;
  font-family: "Inter","Avenir Next","Helvetica Neue", system-ui, sans-serif;
  opacity: 0;
}
.cover-row { display: flex; align-items: baseline; gap: 18px; padding: 11px 0;
  border-bottom: 1px solid rgba(244,247,251,.10); font-size: 28px; }
.cover-row:last-child { border-bottom: none; }
.cover-no { color: var(--ice-blue); font-weight: 800; letter-spacing: .16em; min-width: 60px; }
.cover-song { color: var(--silver-white); font-weight: 700; font-family: "PingFang SC","Noto Sans SC", sans-serif; flex: 1; }
.cover-album { color: rgba(244,247,251,0.58); font-family: "PingFang SC","Noto Sans SC", sans-serif; font-weight: 500; }

.cover-foot { position: absolute; bottom: 78px; left: 0; right: 0; text-align: center;
  font-size: 22px; letter-spacing: .48em; color: rgba(244,247,251,0.45); font-weight: 700;
  font-family: "Inter", sans-serif; }

/* Outro（简化无歌单） */
.outroblk { position: absolute; inset: 0; z-index: 28; opacity: 0;
  background: radial-gradient(ellipse at 50% 40%, #1A2447 0%, var(--night-deep) 70%); }
.outro-title { position: absolute; left: 80px; right: 80px; top: 540px; text-align: center;
  font-size: 88px; line-height: 1.12; font-weight: 800; color: var(--silver-white); letter-spacing: -.02em; }
.outro-cta { position: absolute; left: 100px; right: 100px; top: 920px; text-align: center;
  font-size: 38px; font-weight: 600; color: var(--warm-cream); line-height: 1.5; letter-spacing: .04em; }
.outro-footer { position: absolute; bottom: 110px; left: 0; right: 0; text-align: center;
  font-size: 24px; letter-spacing: .48em; color: rgba(244,247,251,0.45); font-weight: 700;
  font-family: "Inter", sans-serif; }
'''

# 各章节 footage + scrim + corner + album_card + caption
intro_t0 = starts["intro"][0]
voice_start_abs = intro_t0 + COVER_HOLD
list_reveal_at = voice_start_abs + 0.2

# 封面元素
cover_t0 = intro_t0
cover_d = INTRO_D + 0.6  # 延伸进 s1 起始 0.6s，与 s1 footage cross-fade

cover_rows_html = "\n".join(
    f'<div class="cover-row"><span class="cover-no">{s["no"]}</span>'
    f'<span class="cover-song">{s["song"]}</span>'
    f'<span class="cover-album">{s["album"]}</span></div>'
    for s in SONGS
)
# 4 + 3 collage cells
row1_cells = "".join(f'<div class="cv-cell cv-c{i+1}"><span class="nb">{SONGS[i]["no"]}</span></div>' for i in range(4))
row2_cells = "".join(f'<div class="cv-cell cv-c{i+1}"><span class="nb">{SONGS[i]["no"]}</span></div>' for i in range(4, 7))
cover_html = f'''<div id="cover" class="clip cover" data-start="{fmt(cover_t0)}" data-duration="{fmt(cover_d)}" data-track-index="55">
  <div class="cover-grain"></div>
  <div class="cover-eyebrow">ANGELA ZHANG · HIDDEN TRACKS</div>
  <h1 class="cover-title">张韶涵<br/>前7专冷门遗珠</h1>
  <div class="cover-sub">每张专辑，各藏一首宝藏</div>
  <div class="cover-grid">
    <div class="cv-row cv-row1">{row1_cells}</div>
    <div class="cv-row cv-row2">{row2_cells}</div>
  </div>
  <div class="cover-list" id="cover_list">{cover_rows_html}</div>
  <div class="cover-foot">2004 — 2012 · 按专辑顺序</div>
</div>'''

# 章节元素：footage / scrim / corner / album_card / caption
foot_html, scrim_html, corner_html, ac_html, cap_html = [], [], [], [], []
foot_tracks = [0, 6, 0, 6, 0, 6, 0]
for i, s in enumerate(SONGS):
    k = s["key"]
    base = starts[k][0]
    seg_d = starts[k][1]
    a = abs_[k]
    foot_html.append(
        f'<video id="fv_{k}" class="fv clip" data-start="{fmt(base)}" '
        f'data-duration="{fmt(seg_d)}" data-track-index="{foot_tracks[i]}" '
        f'src="clips_seg/{k}.mp4" muted playsinline></video>'
    )
    scrim_html.append(
        f'<div id="sc_{k}" class="clip scrim" data-start="{fmt(base)}" '
        f'data-duration="{fmt(seg_d)}" data-track-index="{12+i}"></div>'
    )
    corner_html.append(
        f'<div id="cn_{k}" class="clip corner" data-start="{fmt(base)}" '
        f'data-duration="{fmt(seg_d)}" data-track-index="{20+i}">'
        f'<span class="pri">{s["song"]}</span><span class="sep">·</span><span class="alb">{s["album"]}</span>'
        f'</div>'
    )
    # 专辑卡：与 footage 同时入场，3.0s 后淡出
    ac_html.append(f'''<div id="ac_{k}" class="clip albumcard" data-start="{fmt(base)}" data-duration="{fmt(ALBUM_CARD_DUR + 0.4)}" data-track-index="{30+i}">
  <div class="albumcard-row">
    <div class="albumcard-index">{s["no"]} / 07</div>
    <div class="albumcard-tag">本专冷门遗珠</div>
  </div>
  <div class="albumcard-song">{s["song"]}</div>
  <div class="albumcard-album">{s["album"]}<span class="year">{s["year"]}</span></div>
  <div class="albumcard-desc">{s["desc"]}</div>
</div>''')
    # 副歌段字幕：避免与 album_card / corner 同时显示，安全间距
    cap_start = base + a["full0"] - base + 5.0  # 章节相对全0 -> 章节相对时间; 改成绝对
    cap_abs = round(starts[k][0] + (a["full0"] - starts[k][0]) + 5.0, 3)
    cap_dur = round(a["full1"] - cap_abs - 0.5, 3)
    if cap_dur < 4: cap_dur = 4
    high_caption_map = {
        "s1": "想去天边，也想自己决定方向。",
        "s2": "不是不抓耳，只是它抓得很轻。",
        "s3": "她也能唱出，带刺的少女感。",
        "s4": "不是找到答案，而是还愿意继续找。",
        "s5": "当年最直接的问题：能不能勇敢说爱。",
        "s6": "不天天想起，但偶尔还是会回来。",
        "s7": "经历以后，还能认回自己。",
    }
    cap_html.append(
        f'<div id="cap_{k}" class="clip caption" data-start="{fmt(cap_abs)}" '
        f'data-duration="{fmt(cap_dur)}" data-track-index="{40+i}">{high_caption_map[k]}</div>'
    )

# Outro 简化（无歌单）
outro_t0 = starts["outro"][0]
outro_d_html = starts["outro"][1]
outro_html = f'''<div id="outroblk" class="clip outroblk" data-start="{fmt(outro_t0)}" data-duration="{fmt(outro_d_html)}" data-track-index="80">
  <div class="outro-title">想听更多被低估的<br/>华语好歌</div>
  <div class="outro-cta">评论区留下你心里的那首遗珠<br/>下期粉丝提名版</div>
  <div class="outro-footer">ANGELA ZHANG · HIDDEN TRACKS</div>
</div>'''

audio_html = f'<audio id="master_audio" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav"></audio>'

# ============ GSAP JS ============
def js_song(s, i):
    k = s["key"]
    a = abs_[k]
    base = a["seg_start"]; end = a["seg_end"]
    return f'''
// ---- {s["song"]} ----
tl.fromTo("#fv_{k}", {{opacity:0, scale:1.04}}, {{opacity:1, scale:1.0, duration:1.0, ease:"power2.out"}}, {fmt(base)});
tl.to("#sc_{k}", {{opacity:1, duration:1.0, ease:"power1.out"}}, {fmt(base)});
// 角标与专辑卡同时入场（与 footage）
tl.fromTo("#cn_{k}", {{opacity:0, y:-12}}, {{opacity:1, y:0, duration:.55, ease:"power2.out"}}, {fmt(base+0.2)});
tl.fromTo("#ac_{k}", {{opacity:0, y:36, scale:0.96}}, {{opacity:1, y:0, scale:1.0, duration:.7, ease:"power3.out"}}, {fmt(base+0.15)});
tl.to("#ac_{k}", {{opacity:0, y:-18, duration:.55, ease:"power2.in"}}, {fmt(base + ALBUM_CARD_DUR - 0.05)});
tl.set("#ac_{k}", {{opacity:0}}, {fmt(base + ALBUM_CARD_DUR + 0.05)});
// 副歌字幕
tl.fromTo("#cap_{k}", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:.65, ease:"power2.out"}}, {fmt(a["full0"]+5.0)});
tl.to("#cap_{k}", {{opacity:0, y:-8, duration:.55, ease:"power2.in"}}, {fmt(a["full1"]-1.0)});
tl.set("#cap_{k}", {{opacity:0}}, {fmt(a["full1"])});
// 段尾淡出
tl.to("#fv_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(end-1.0)});
tl.set("#fv_{k}", {{opacity:0}}, {fmt(end)});
tl.to("#sc_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(end-1.0)});
tl.set("#sc_{k}", {{opacity:0}}, {fmt(end)});
tl.to("#cn_{k}", {{opacity:0, duration:.6, ease:"power1.in"}}, {fmt(end-0.6)});
tl.set("#cn_{k}", {{opacity:0}}, {fmt(end)});
'''

JS = f'''
// 首屏封面 t=0 全 opacity:1
tl.set("#cover", {{opacity:1}}, 0);
tl.set(".cover-title", {{opacity:1}}, 0);
tl.set(".cover-sub", {{opacity:1}}, 0);
tl.set(".cover-grid", {{opacity:1}}, 0);
tl.set(".cover-eyebrow", {{opacity:1}}, 0);
tl.set(".cover-foot", {{opacity:1}}, 0);
// 微动：标题轻呼吸
tl.to(".cover-title", {{scale:1.012, duration:2.4, yoyo:true, repeat:1, ease:"sine.inOut"}}, 1.0);
// 旁白起时列表淡入
tl.fromTo("#cover_list", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:.9, ease:"power3.out"}}, {fmt(list_reveal_at)});
// 封面淡出：从 s1 章节开始（cover_t0 + INTRO_D）淡出到 s1 + 0.6s（与 s1 footage cross-fade）
tl.to("#cover", {{opacity:0, duration:.6, ease:"power2.in"}}, {fmt(cover_t0+INTRO_D)});
tl.set("#cover", {{opacity:0}}, {fmt(cover_t0+INTRO_D+0.6)});

{''.join(js_song(s, i) for i, s in enumerate(SONGS))}

// Outro
tl.fromTo("#outroblk", {{opacity:0}}, {{opacity:1, duration:.8, ease:"power2.out"}}, {fmt(outro_t0)});
tl.to("#outroblk", {{opacity:1, duration:.1}}, {fmt(TOTAL-0.2)});
'''

grain_html = f'<div id="grain" class="clip grain" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="2"></div>'

html = f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
  <div id="root" data-composition-id="zhang-shaohan-7albums" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
    {chr(10).join(foot_html)}
    {grain_html}
    {chr(10).join(scrim_html)}
    {chr(10).join(corner_html)}
    {chr(10).join(ac_html)}
    {chr(10).join(cap_html)}
    {cover_html}
    {outro_html}
    {audio_html}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    {JS}
    window.__timelines["zhang-shaohan-7albums"] = tl;
  </script>
</body>
</html>
'''

Path(f"{HF}/index.html").write_text(html, encoding="utf-8")
Path(f"{HF}/meta.json").write_text(
    '{"id":"zhang-shaohan-7albums","name":"张韶涵前7张专辑·冷门遗珠盘点 v2"}',
    encoding="utf-8"
)
print(f"hf/index.html written ({len(html)} bytes), TOTAL={TOTAL}s")
print("Next: cd hf && npm run check && npm run render -- --sdr")
