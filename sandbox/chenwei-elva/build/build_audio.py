#!/usr/bin/env python3
"""样片 master.wav：封面 + 开头(op1-6) + 第8首《没有人》(rj1-4 + 转场 tr1)。
《没有人》整首做底：开头/进入旁白期低音乐床(duck)，到副歌 swell 推满，
副歌展示段音频 = 与展示视频同一 MV 窗口(源 200s 起) → 口型天然同步。
导出 timeline.json 供 build_html.py 复用同一时间轴。从项目根运行：python3 build/build_audio.py
"""
import subprocess, wave, contextlib, json
from pathlib import Path

A = "audio"
MUSIC_RAW = "raw/meiyouren_full.wav"     # 288s 全曲（与展示视频同一 MV 录音）
MUSIC = "build/segs/music_norm.wav"      # loudnorm I=-14 后的全曲

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(c): subprocess.run(c, check=True)

Path("build/segs").mkdir(parents=True, exist_ok=True)
# 预归一化音乐到 I=-14（副歌段落落 ~-14dB）
run(["ffmpeg","-v","error","-i",MUSIC_RAW,"-af",
     "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000","-ac","2","-ar","48000",MUSIC,"-y"])

KEYS = ["op1","op2","op3","op4","op5","op6","rj1","rj2","rj3","rj4","tr1"]
d = {k: dur(f"{A}/{k}.wav") for k in KEYS}

# ---------------- 主时间轴 ----------------
COVER_D = 5.0
LEAD = 0.6
t = COVER_D + LEAD
starts = {}
def place(key, gap):
    global t
    starts[key] = round(t, 3)
    t += d[key] + gap
    return starts[key]

place("op1", 0.7); place("op2", 0.7); place("op3", 0.6); place("op4", 0.7)
place("op5", 1.0)          # 留 screenA"声音系统"消化位
place("op6", 1.5)
OPEN_END = round(t, 3)
ENTRY_START = round(t, 3)
t += LEAD
place("rj1", 0.8); place("rj2", 0.65); place("rj3", 0.65); place("rj4", 0.0)
POST, SWELL, SHOW_D = 1.2, 1.5, 30.0
t += POST
SWELL_START = round(t, 3)
t += SWELL
SHOW_START = round(t, 3)
t += SHOW_D
SHOW_END = round(t, 3)
TR_START = round(SHOW_END - 0.3, 3)
starts["tr1"] = TR_START
TR_END = round(TR_START + d["tr1"], 3)
TOTAL = round(TR_END + 1.0, 3)

# 音乐同步：源 200s（展示副歌起点）落在 SHOW_START
MV_SHOW = 200.0
T0 = round(MV_SHOW - SHOW_START, 3)
assert T0 >= 0, f"T0={T0} <0 — showcase 起点晚于源 200s，需提前"
print(f"SHOW_START={SHOW_START}  music T0={T0}  TOTAL={TOTAL} ({TOTAL//60:.0f}:{TOTAL%60:05.2f})")

# ---------------- 音量包络（music_norm[T0..] 上，master t 的函数）----------------
B, F, L = 0.30, 1.0, 0.28           # 床 / 满 / 转场低
fd1 = round(SHOW_END + 1.25, 3)     # 副歌后淡降到 L
fd2 = round(TR_END + 0.3, 3)        # 转场尾开始淡出
ve = (
    f"(lt(t,1.2))*({B}*t/1.2)"
    f"+(between(t,1.2,{SWELL_START}))*{B}"
    f"+(between(t,{SWELL_START},{SHOW_START}))*({B}+({F}-{B})*(t-{SWELL_START})/{SWELL})"
    f"+(between(t,{SHOW_START},{SHOW_END}))*{F}"
    f"+(between(t,{SHOW_END},{fd1}))*({F}+({L}-{F})*(t-{SHOW_END})/({fd1}-{SHOW_END}))"
    f"+(between(t,{fd1},{fd2}))*{L}"
    f"+(gte(t,{fd2}))*max(0,{L}-{L}*(t-{fd2})/({TOTAL}-{fd2}))"
)

# ---------------- 分阶段构建 ----------------
# 1) voice.wav：各句 loudnorm + adelay 后 amix（互不重叠）
v_inputs = sum([["-i", f"{A}/{k}.wav"] for k in KEYS], [])
v_fc, v_labels = [], []
for i, k in enumerate(KEYS):
    ms = int(round(starts[k] * 1000))
    v_fc.append(
        f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,adelay={ms}|{ms}[a{i}]")
    v_labels.append(f"[a{i}]")
v_fc.append(f"{''.join(v_labels)}amix=inputs={len(KEYS)}:normalize=0:duration=longest[v]")
run(["ffmpeg","-v","error", *v_inputs, "-filter_complex", ";".join(v_fc),
     "-map","[v]","-ac","2","-ar","48000","build/segs/voice.wav","-y"])

# 2) music.wav：全曲从 T0 起，按 master 时间施加音量包络
run(["ffmpeg","-v","error","-i", MUSIC, "-filter_complex",
     f"[0:a]atrim={T0}:{round(T0+TOTAL,3)},asetpts=PTS-STARTPTS,aresample=48000,"
     f"aformat=channel_layouts=stereo,volume='{ve}':eval=frame[m]",
     "-map","[m]","-ac","2","-ar","48000","build/segs/music.wav","-y"])

# 3) master.wav：voice + music
run(["ffmpeg","-v","error","-i","build/segs/voice.wav","-i","build/segs/music.wav",
     "-filter_complex","[0:a][1:a]amix=inputs=2:normalize=0:duration=longest,"
     f"atrim=0:{TOTAL},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "planned:", TOTAL)

# ---------------- timeline.json ----------------
TL = dict(
    COVER_D=COVER_D, OPEN_END=OPEN_END, ENTRY_START=ENTRY_START,
    SWELL_START=SWELL_START, SHOW_START=SHOW_START, SHOW_END=SHOW_END,
    SHOW_D=SHOW_D, TR_START=TR_START, TR_END=TR_END, TOTAL=TOTAL,
    starts=starts, durs=d,
)
Path("timeline.json").write_text(json.dumps(TL, ensure_ascii=False, indent=2), encoding="utf-8")
import shutil
shutil.copy("master.wav", "hf/master.wav")
print("timeline.json + hf/master.wav written")
