# -*- coding: utf-8 -*-
"""从伤痕到玫瑰：李宗盛写透了林忆莲 — 竖屏长篇叙事时间线 (8首 8->1)。
产物: master.wav (逐段 床->voice(duck)->swell->副歌展示->转场) + hf/index.html + hf/clips_seg/*.mp4。
SAMPLE=1 只出 cover+intro+第8首(+转场tease)，供样片审风格。
渲染后必须 ffmpeg mux master.wav。
"""
import os, sys, json, wave, contextlib, shutil, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import content

SAMPLE = os.environ.get("SAMPLE") == "1"
HTML_ONLY = os.environ.get("HTML_ONLY") == "1"   # 只重生成 index.html(audio/clips_seg复用)
AUDIO_ONLY = os.environ.get("AUDIO_ONLY") == "1" # 只重建 master.wav(视频/HTML复用)→改响度后 re-mux
C = "clips"

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes()/w.getframerate(), 3)

def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

# ---------- 节奏常量 ----------
LEAD       = 0.15
PRE_VOICE  = 0.8
POST_VOICE = 1.2
SWELL      = 1.6
BED        = 0.22          # voice 期音乐床
TRANS_GAP  = 0.5           # 副歌结束到转场旁白的小落差
TRANS_TAIL = 1.2           # 转场后尾
COVER_D    = 4.6
INTRO_TAIL = 2.0
OUTRO_TAIL = 4.0

# ---------- 每首：源片 / 副歌源时间码 / 展示时长 / 配色 ----------
# chorus = 源中"副歌(展示段)"起点的秒数；mseek = chorus - full0 (使副歌恰好落在 swell 顶)
SRC = {
  # chorus = 源中副歌(展示段)起点秒;mseek=chorus-full0 使副歌落在 swell 顶。展示窗均经抽帧核验落在林忆莲特写(s4为官方Comix)。
  "s8": dict(clip="vert_s8", chorus=196.0, show=30.0,
             pri="#E7C8A0", acc="#C8324A", bg="#160B0E", tintA="rgba(60,12,18,.30)", tintB="rgba(120,40,30,.10)"),
  "s7": dict(clip="vert_s7", chorus=195.0, show=30.0, pri="#BFC8D6", acc="#7E8CA8", bg="#0B0E16", tintA="rgba(20,30,55,.34)", tintB="rgba(40,50,80,.10)"),
  "s6": dict(clip="vert_s6", chorus=150.0, show=30.0, pri="#AEC2D8", acc="#5E7FB0", bg="#080E18", tintA="rgba(15,35,70,.36)", tintB="rgba(30,55,95,.10)"),
  # s5 不许哭：footage=《哭》官方MV(粤,视觉),music=不许哭官方音源(国,解耦)。烧词已裁→无错词。
  "s5": dict(clip="vert_s5", chorus=110.0, show=30.0, audio_src="raw/yt_s5_audio.wav", audio_chorus=145.0,
             pri="#CFCAC2", acc="#9A8E80", bg="#0A0A0C", tintA="rgba(10,10,12,.42)", tintB="rgba(40,38,36,.10)"),
  "s4": dict(clip="vert_s4", chorus=200.0, show=30.0, pri="#E6A6B0", acc="#C8324A", bg="#140810", tintA="rgba(70,10,30,.34)", tintB="rgba(150,30,60,.12)"),
  "s3": dict(clip="vert_s3", chorus=216.0, show=30.0, mgain=1.62, pri="#A9BEE0", acc="#4E6CC0", bg="#070B18", tintA="rgba(12,24,60,.38)", tintB="rgba(30,50,110,.12)"),  # 夜太黑暗调偏轻→补
  "s2": dict(clip="vert_s2", chorus=150.0, show=34.0, mgain=1.20, pri="#E2B0A8", acc="#C8324A", bg="#140909", tintA="rgba(60,12,14,.36)", tintB="rgba(130,35,30,.10)"),
  "s1": dict(clip="vert_s1", chorus=150.0, show=46.0, pri="#F0D49A", acc="#D43A4E", bg="#160A0C", tintA="rgba(70,16,20,.26)", tintB="rgba(190,60,40,.12)"),
}

SONGS = content.SONGS
BY_KEY = {s["key"]: s for s in SONGS}
KEYS = ["s8"] if SAMPLE else [s["key"] for s in SONGS]  # 叙事序

# ---------- 旁白时长 ----------
def nd(k):
    p = Path("audio")/f"{k}.wav"
    return dur(p) if p.exists() else 0.0
NARR = {"intro": nd("intro")}
for k in KEYS:
    NARR[f"{k}_v"] = nd(f"{k}_v")
    NARR[f"{k}_t"] = nd(f"{k}_t")
if not SAMPLE:
    NARR["outro"] = nd("outro"); NARR["cta"] = nd("cta")

# ---------- 每首段锚点(段内相对时间) ----------
def anchors(k):
    v_d = NARR[f"{k}_v"]; t_d = NARR.get(f"{k}_t", 0.0)
    show = SRC[k]["show"]
    v0 = LEAD + PRE_VOICE
    v1 = v0 + v_d
    sw0 = v1 + POST_VOICE
    full0 = sw0 + SWELL
    full1 = full0 + show
    if t_d > 0:
        t0 = full1 + TRANS_GAP
        t1 = t0 + t_d
        end = t1 + TRANS_TAIL
    else:
        t0 = t1 = full1
        end = full1 + TRANS_TAIL
    return dict(v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1, t0=t0, t1=t1, end=end, seg=round(end,3))

# ---------- 段时长 & 主轴起点 ----------
intro_seg = round(LEAD + 0.4 + NARR["intro"] + INTRO_TAIL, 3)
seg_len = {k: anchors(k)["seg"] for k in KEYS}
outro_seg = round(LEAD + NARR.get("outro", 0) + 0.9 + NARR.get("cta", 0) + OUTRO_TAIL, 3) if not SAMPLE else 0.0

starts = {}
t = 0.0
starts["cover"] = (0.0, COVER_D); t += COVER_D
starts["intro"] = (t, intro_seg); t += intro_seg
for k in KEYS:
    starts[k] = (round(t,3), seg_len[k]); t += seg_len[k]
if not SAMPLE:
    starts["outro"] = (round(t,3), outro_seg); t += outro_seg
TOTAL = round(t, 3)
print(f"SAMPLE={SAMPLE} TOTAL={TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")
for k in (["cover","intro"]+KEYS+(["outro"] if not SAMPLE else [])):
    print(f"  {k:7s} start={starts[k][0]:8.2f} dur={starts[k][1]:7.2f}")

# ============ 音频 ============
SEG = Path("build/segs"); SEG.mkdir(parents=True, exist_ok=True)
LN = "loudnorm=I=-14:TP=-1.0:LRA=11"

def vol_env(a):
    """音乐音量包络: 进入0 -> 床 -> swell -> 满 -> (转场)降回床 -> 尾0。afade 尾另做。"""
    v0, sw0, full0, full1, t0, t1, end = a["v0"], a["sw0"], a["full0"], a["full1"], a["t0"], a["t1"], a["end"]
    has_t = t1 > full1
    e = (f"(lt(t,{LEAD}))*0"
         f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{max(v0-LEAD,0.01)})"
         f"+(between(t,{v0},{sw0}))*{BED}"
         f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})")
    if has_t:
        e += (f"+(between(t,{full0},{full1}))*1.0"
              f"+(between(t,{full1},{t0}))*(1.0-{1.0-BED}*(t-{full1})/{max(t0-full1,0.01)})"
              f"+(gte(t,{t0}))*{BED}")
    else:
        e += f"+(gte(t,{full0}))*1.0"
    return e

def build_song_seg(k):
    a = anchors(k); seg = a["seg"]
    clip = SRC[k]["clip"]
    foot_mseek = max(SRC[k]["chorus"] - a["full0"], 0.0)
    SRC[k]["mseek"] = foot_mseek          # precut footage 用这个
    # 音乐源：解耦曲(s5)用独立官方音源,否则用 footage clip 自带音轨(口型同步)
    if SRC[k].get("audio_src"):
        mus_file = SRC[k]["audio_src"]; mseek = max(SRC[k]["audio_chorus"] - a["full0"], 0.0)
    else:
        mus_file = f"{C}/{clip}.mp4"; mseek = foot_mseek
    fo_start = a["t1"] if a["t1"] > a["full1"] else a["full1"]
    voice_at = a["v0"]
    inputs = ["-i", mus_file, "-i", f"audio/{k}_v.wav"]
    mg = SRC[k].get("mgain", 1.0)
    fc = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[vo];"
          f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{LN},atrim={mseek}:{mseek+seg},asetpts=PTS-STARTPTS,"
          f"volume='{vol_env(a)}':eval=frame,volume={mg},afade=t=out:st={fo_start}:d={max(seg-fo_start,0.4)}[mus];")
    mix = "[vo][mus]"
    if a["t1"] > a["full1"]:
        inputs += ["-i", f"audio/{k}_t.wav"]
        fc += f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(a['t0']*1000)}|{int(a['t0']*1000)},volume=2.0[tr];"
        mix = "[vo][tr][mus]"
        n = 3
    else:
        n = 2
    fc += f"{mix}amix=inputs={n}:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95:level=disabled[out]"
    run(["ffmpeg","-v","error",*inputs,"-filter_complex",fc,"-map","[out]","-ac","2","-ar","48000",str(SEG/f"seg_{k}.wav"),"-y"])

# intro: 用 s8《当爱已成往事》霸王别姬前奏(0s起)作低床
def build_intro():
    voice_at = LEAD + 0.4
    run(["ffmpeg","-v","error","-i", f"{C}/vert_s8.mp4","-i","audio/intro.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[vo];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{LN},atrim=0:{intro_seg},asetpts=PTS-STARTPTS,volume=0.17,"
         f"afade=t=in:st=0:d=1.4,afade=t=out:st={intro_seg-1.6}:d=1.6[bed];"
         f"[vo][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_seg},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",str(SEG/"seg_intro.wav"),"-y"])

# cover: 低床(s8 副歌段)
def build_cover():
    run(["ffmpeg","-v","error","-i", f"{C}/vert_s8.mp4","-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{LN},atrim=196:{196+COVER_D},asetpts=PTS-STARTPTS,volume=0.16,"
         f"afade=t=in:st=0:d=1.0,afade=t=out:st={COVER_D-1.2}:d=1.2[out]",
         "-map","[out]","-ac","2","-ar","48000",str(SEG/"seg_cover.wav"),"-y"])

# outro + 固定 CTA (full only)
def build_outro():
    vat = LEAD
    cta_at = LEAD + NARR["outro"] + 0.9
    run(["ffmpeg","-v","error","-i", f"{C}/vert_s1.mp4","-i","audio/outro.wav","-i","audio/cta.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(vat*1000)}|{int(vat*1000)},volume=2.0[vo];"
         f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_at*1000)}|{int(cta_at*1000)},volume=2.0[cta];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{LN},atrim={SRC['s1']['chorus']}:{SRC['s1']['chorus']+outro_seg},asetpts=PTS-STARTPTS,volume=0.20,"
         f"afade=t=in:st=0:d=1.0,afade=t=out:st={outro_seg-1.6}:d=1.6[bed];"
         f"[vo][cta][bed]amix=inputs=3:normalize=0:duration=longest,atrim=0:{outro_seg},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",str(SEG/"seg_outro.wav"),"-y"])

HF = Path("hf"); HF.mkdir(exist_ok=True)
def precut(out, src, seek, length):
    # CRF 高一点 + 软 SD letterbox → 文件小（HF 把 footage base64 内联进 HTML，过大 Chrome 卡死超时）
    run(["ffmpeg","-v","error","-i",src,"-ss",str(seek),"-t",str(length),
         "-c:v","libx264","-preset","fast","-crf","33","-r","30","-g","30","-keyint_min","30","-an",
         "-vf","scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2","-movflags","+faststart",str(out),"-y"])

if HTML_ONLY:
    # 仅重生成 HTML（audio/clips_seg 已有）；仍需算各首 footage mseek 供一致性
    for k in KEYS:
        SRC[k]["mseek"] = max(SRC[k]["chorus"] - anchors(k)["full0"], 0.0)
    print("HTML_ONLY: 跳过 audio + precut")
else:
    build_cover(); build_intro()
    for k in KEYS:
        print("  audio", k); build_song_seg(k)
    if not SAMPLE: build_outro()
    order = ["cover","intro"]+KEYS+(["outro"] if not SAMPLE else [])
    (SEG/"seglist.txt").write_text("".join(f"file 'seg_{k}.wav'\n" for k in order), encoding="utf-8")
    run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(SEG/"seglist.txt"),"-ac","2","-ar","48000","master.wav","-y"])
    print("master dur:", dur("master.wav"), "planned:", TOTAL)
    shutil.copy("master.wav", "hf/master.wav")
    if not AUDIO_ONLY:
        # 渲染用静音占位(render 不需真音频→mux 时换回 master.wav;避免 100MB+ wav 内联卡死 Chrome)
        run(["ffmpeg","-v","error","-f","lavfi","-i","anullsrc=r=48000:cl=stereo","-t",str(TOTAL),"-c:a","aac","-b:a","8k",str(HF/"silent.m4a"),"-y"])
        # ---- 预切 footage (HF 不能控 currentTime) ----
        (HF/"clips_seg").mkdir(exist_ok=True)
        precut(HF/"clips_seg/intro.mp4", f"{C}/vert_s8.mp4", 36.0, intro_seg)  # intro 背景=s8红衣慢镜
        for k in KEYS:
            precut(HF/f"clips_seg/{k}.mp4", f"{C}/{SRC[k]['clip']}.mp4", SRC[k]["mseek"], anchors(k)["seg"])
        if not SAMPLE:
            precut(HF/"clips_seg/outro.mp4", f"{C}/vert_s1.mp4", SRC["s1"]["chorus"], outro_seg)
        print("clips_seg + master copied")
    else:
        print("AUDIO_ONLY: master.wav rebuilt (skip precut/html)")

# ============ HTML ============
if not AUDIO_ONLY:
    import html_gen
    html_gen.write_html(starts, KEYS, SRC, BY_KEY, content, NARR,
                        dict(COVER_D=COVER_D, intro_seg=intro_seg, outro_seg=outro_seg,
                             TOTAL=TOTAL, SAMPLE=SAMPLE), anchors)
print("done")
