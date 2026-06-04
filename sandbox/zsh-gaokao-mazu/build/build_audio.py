#!/usr/bin/env python3
"""master.wav 构建：cover/intro/4part/outro。
每 part：该曲音轨从 (chorus_peak - scene_dur) 拉起 → 旁白期低音乐床(BED) → swell → 副歌全量(SHOW) → fade。
旁白(女声)叠在床上(自然 ducking)。逐段 loudnorm=I=-14 统一响度。渲染后必须 mux 本 master。
同时输出 build/timeline.json 供 HTML 构建读。"""
import subprocess, wave, contextlib, json
from pathlib import Path

A = "audio"
def runf(c): subprocess.run(c, check=True)
def dwav(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes()/w.getframerate(), 3)

# ---- 常量 ----
LEAD=0.3; DIGEST=1.3; SWELL=1.5; BED=0.20; TAIL=1.2; GAP=0.4
COVER_D=3.5; INTRO_TAIL=2.6; OUTRO_TAIL=3.0
VOL_VOICE=2.0
SR=48000

Path("build/segs").mkdir(parents=True, exist_ok=True)

# ---- 歌曲音轨源 + 副歌起点 + SHOW ----
SONG = {
 "p1": dict(src="raw/s1_pojian_mv.mp4", peak=52.0, show=27.0, mg=0.70),  # 破茧动画压缩重→压
 "p2": dict(src="raw/s2_pianzhang.mp4", peak=68.0, show=28.0, mg=1.33),  # 篇章live偏轻→抬
 "p3": dict(src="raw/s3_linyu_yt.mkv", peak=58.0, show=27.0, mg=1.02),
 "p4": dict(src="raw/s4_yinxing_hd.mkv", peak=80.0, show=30.0, mg=0.94),
}

# ---- 1. 合成各 part 旁白 (trans + gap + sN)；p1 = s1 ----
def combine(out, segs):
    # segs: ["trans1","s2"] → trans + GAP静音 + s2
    parts = []
    for i, s in enumerate(segs):
        parts.append(("-i", f"{A}/{s}.wav"))
    n = len(segs)
    inputs = []
    for s in segs:
        inputs += ["-i", f"{A}/{s}.wav"]
    # 插 GAP 静音：用 concat + anullsrc
    fc = []
    idx = 0
    chain = ""
    # 构造 [0][sil][1][sil]... concat
    sil_idx = n
    cmd = ["ffmpeg","-v","error"]
    for s in segs:
        cmd += ["-i", f"{A}/{s}.wav"]
    cmd += ["-f","lavfi","-t",str(GAP),"-i","anullsrc=r=24000:cl=mono"]
    seq = ""
    cnt = 0
    for i in range(n):
        seq += f"[{i}:a]"
        cnt += 1
        if i != n-1:
            seq += f"[{n}:a]"   # silence input index = n
            cnt += 1
    seq += f"concat=n={cnt}:v=0:a=1[a]"
    cmd += ["-filter_complex", seq, "-map","[a]","-ar","24000", f"{A}/{out}.wav","-y"]
    runf(cmd)
    return dwav(f"{A}/{out}.wav")

VOICE = {}
VOICE["p1"] = dwav(f"{A}/s1.wav")  # p1 直接用 s1
import shutil; shutil.copy(f"{A}/s1.wav", f"{A}/voice_p1.wav")
VOICE["p2"] = combine("voice_p2", ["trans1","s2"])
VOICE["p3"] = combine("voice_p3", ["trans2","s3"])
VOICE["p4"] = combine("voice_p4", ["trans3","s4"])
INTRO_V = dwav(f"{A}/intro.wav")
OUTRO_V = dwav(f"{A}/outro.wav")
print("VOICE durs:", VOICE, "intro", INTRO_V, "outro", OUTRO_V)

# ---- 2. 时间轴 ----
def scene_dur(part): return round(LEAD + VOICE[part] + DIGEST, 3)
SEG = {}
SEG["cover"] = COVER_D
SEG["intro"] = round(LEAD + INTRO_V + INTRO_TAIL, 3)
for p in ["p1","p2","p3","p4"]:
    SEG[p] = round(scene_dur(p) + SONG[p]["show"] + TAIL, 3)
SEG["outro"] = round(LEAD + OUTRO_V + OUTRO_TAIL, 3)

order = ["cover","intro","p1","p2","p3","p4","outro"]
start = {}; t = 0.0
for k in order:
    start[k] = round(t,3); t += SEG[k]
TOTAL = round(t,3)
print("SEG:", json.dumps(SEG, indent=1)); print("TOTAL:", TOTAL, f"= {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ---- 3. 构建各段 wav ----
def bed_only(out, src, sk, seg_len, vol, fin, fout):
    runf(["ffmpeg","-v","error","-i",src,"-filter_complex",
      f"[0:a]aresample={SR},aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
      f"atrim={sk}:{sk+seg_len},asetpts=PTS-STARTPTS,volume={vol},"
      f"afade=t=in:st=0:d={fin},afade=t=out:st={seg_len-fout}:d={fout}[a]",
      "-map","[a]","-ac","2","-ar",str(SR),"-t",str(seg_len),f"build/segs/seg_{out}.wav","-y"])

def part_seg(part):
    s = SONG[part]; sd = scene_dur(part); seg_len = SEG[part]
    peak = s["peak"]; show = s["show"]; mstart = round(peak - sd, 3)
    voice_at = LEAD
    swell0 = round(sd - SWELL, 3)
    full0 = sd
    full1 = round(sd + show, 3)
    # 音乐音量包络
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{LEAD+0.6}))*({BED}*(t-{LEAD})/0.6)"
          f"+(between(t,{LEAD+0.6},{swell0}))*{BED}"
          f"+(between(t,{swell0},{full0}))*({BED}+{1.0-BED}*(t-{swell0})/{SWELL})"
          f"+(gte(t,{full0}))*1.0")
    runf(["ffmpeg","-v","error","-i",s["src"],"-i",f"{A}/voice_{part}.wav",
      "-filter_complex",
      f"[1:a]aresample={SR},aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume={VOL_VOICE}[voice];"
      f"[0:a]aresample={SR},aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
      f"atrim={mstart}:{mstart+seg_len},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,volume={s['mg']},"
      f"afade=t=out:st={full1}:d={seg_len-full1}[music];"
      f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.95[a]",
      "-map","[a]","-ac","2","-ar",str(SR),f"build/segs/seg_{part}.wav","-y"])
    return dict(scene_dur=sd, show=show, mstart=mstart, peak=peak)

# cover: 隐形钢琴前奏低床
bed_only("cover", SONG["p4"]["src"], 4.0, COVER_D, 0.16, 1.0, 1.0)

# intro: 破茧 verse 低床(building) + 旁白 + 末尾铃声
# 先做铃声(两声 chime)
runf(["ffmpeg","-v","error","-f","lavfi","-i","sine=frequency=988:duration=0.9",
      "-af","afade=t=out:st=0.05:d=0.85,volume=0.42","-ar",str(SR),"-ac","2","build/segs/bell1.wav","-y"])
intro_len = SEG["intro"]
bell_at = round(LEAD + INTRO_V + 0.3, 3)  # 旁白后铃声
ve_i = (f"(lt(t,{LEAD}))*0"
        f"+(between(t,{LEAD},{LEAD+1.0}))*(0.17*(t-{LEAD})/1.0)"
        f"+(between(t,{LEAD+1.0},{intro_len-INTRO_TAIL}))*0.17"
        f"+(gte(t,{intro_len-INTRO_TAIL}))*(0.17+0.55*(t-{intro_len-INTRO_TAIL})/{INTRO_TAIL})")
runf(["ffmpeg","-v","error","-i",SONG["p1"]["src"],"-i",f"{A}/intro.wav","-i","build/segs/bell1.wav",
  "-filter_complex",
  f"[1:a]aresample={SR},aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOL_VOICE}[voice];"
  f"[2:a]adelay={int(bell_at*1000)}|{int(bell_at*1000)}[bell];"
  f"[0:a]aresample={SR},aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
  f"atrim=26:{26+intro_len},asetpts=PTS-STARTPTS,volume='{ve_i}':eval=frame[music];"
  f"[music][voice]amix=inputs=2:normalize=0:duration=longest[m1];"
  f"[m1][bell]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_len},alimiter=limit=0.95[a]",
  "-map","[a]","-ac","2","-ar",str(SR),"build/segs/seg_intro.wav","-y"])

PA = {}
for p in ["p1","p2","p3","p4"]:
    print("building", p); PA[p] = part_seg(p)

# outro: 隐形 final chorus 低床(情绪) + 旁白
outro_len = SEG["outro"]
ve_o = (f"(between(t,0,1.2))*(0.22*t/1.2)+(between(t,1.2,{outro_len-2.5}))*0.22+(gte(t,{outro_len-2.5}))*(0.22*(1-(t-{outro_len-2.5})/2.5))")
runf(["ffmpeg","-v","error","-i",SONG["p4"]["src"],"-i",f"{A}/outro.wav",
  "-filter_complex",
  f"[1:a]aresample={SR},aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOL_VOICE}[voice];"
  f"[0:a]aresample={SR},aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
  f"atrim=150:{150+outro_len},asetpts=PTS-STARTPTS,volume='{ve_o}':eval=frame[music];"
  f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_len},alimiter=limit=0.95[a]",
  "-map","[a]","-ac","2","-ar",str(SR),"build/segs/seg_outro.wav","-y"])

# ---- 4. 拼 master ----
Path("build/segs/list.txt").write_text("".join(f"file 'seg_{k}.wav'\n" for k in order), encoding="utf-8")
runf(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/list.txt","-ac","2","-ar",str(SR),"master.wav","-y"])
import shutil as sh; sh.copy("master.wav","hf/master.wav")
print("master dur:", dwav("master.wav"), "planned:", TOTAL)

# ---- 5. timeline.json ----
tl = dict(total=TOTAL, cover_d=COVER_D, order=order, start=start, seg=SEG,
          intro=dict(lead=LEAD, voice=INTRO_V, tail=INTRO_TAIL),
          outro=dict(lead=LEAD, voice=OUTRO_V, tail=OUTRO_TAIL),
          parts={p: dict(scene_dur=PA[p]["scene_dur"], show=PA[p]["show"],
                          song_clip=f"clips_seg/song_{p.replace('p','s')}.mp4",
                          scene_clip=f"clips_seg/scene_{p}.mp4") for p in ["p1","p2","p3","p4"]},
          lead=LEAD, digest=DIGEST, swell=SWELL, tail=TAIL)
Path("build/timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
print("timeline.json written")
print("AUDIO BUILD DONE")
