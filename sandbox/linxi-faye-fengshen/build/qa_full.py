#!/usr/bin/env python3
"""一次性全片 QA：每块抽 3 帧拼网格（封面/标题卡/展示段/转场）+ 全片静音 + 逐首副歌响度。
产物：qa_frames/QA_grid{1,2,3}.png（供 Read 逐张看）+ 终端报告。
从项目根运行：python3 build/qa_full.py
"""
import json, subprocess
from pathlib import Path
M = "renders/linxi-faye-fengshen-full.mp4"
bj = json.loads(Path("hf_full/blocks.json").read_text())
order = bj["blocks"]; durs = bj["durs"]
start = {}; t = 0.0
for b in order: start[b] = round(t,3); t += durs[b]

def frame(at, out):
    subprocess.run(["ffmpeg","-y","-ss",f"{at:.2f}","-i",M,"-frames:v","1","-vf","scale=360:640",out,"-v","error"])

# 3 frames per block: entry/title, showcase, transition/pullquote
labels=[]
for b in order:
    s=start[b]; d=durs[b]
    pts=[s+5.0, s+d*0.60, s+d*0.90] if b not in ("intro","outro") else [s+2.0, s+d*0.5, s+d*0.85]
    for i,p in enumerate(pts):
        frame(min(p, s+d-0.5), f"qa_frames/QF_{b}_{i}.png")
    labels.append(b)

# grids: 4 blocks (=12 frames, 4 rows x 3) per sheet → 3 sheets
def grid(blocks, out):
    ins=[];
    for b in blocks:
        for i in range(3): ins+=["-i",f"qa_frames/QF_{b}_{i}.png"]
    rows="".join(f"[{r*3}][{r*3+1}][{r*3+2}]hstack=3[r{r}];" for r in range(len(blocks)))
    stack="".join(f"[r{r}]" for r in range(len(blocks)))+f"vstack={len(blocks)}[v]"
    subprocess.run(["ffmpeg","-y",*ins,"-filter_complex",rows+stack,"-map","[v]",out,"-v","error"])

grid(order[0:4], "qa_frames/QA_grid1.png")   # intro s10 s9 s8
grid(order[4:8], "qa_frames/QA_grid2.png")   # s7 s6 s5 s4
grid(order[8:12],"qa_frames/QA_grid3.png")   # s3 s2 s1 outro
print("grids: QA_grid1 =", order[0:4], "| QA_grid2 =", order[4:8], "| QA_grid3 =", order[8:12])

# audio: silence + per-showcase loudness
print("\n=== silence >1.5s @-34dB (mux'd final) ===")
r=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",M,"-af","silencedetect=n=-34dB:d=1.5","-f","null","/dev/null"],capture_output=True,text=True).stderr
sil=[l for l in r.splitlines() if "silence_start" in l or "silence_duration" in l]
print("\n".join(sil) if sil else "none ✓")

print("\n=== per-song showcase loudness (target ~-14, spread <3dB) ===")
D=json.load(open("audio_full/durs.json")); GAP=0.55;POST=1.0;SWELL=1.5;RAMP=0.8
NARR={"s10":4,"s9":3,"s8":3,"s7":3,"s6":3,"s5":3,"s4":3,"s3":3,"s2":3,"s1":5}
KEYS={"s10":["s10_1","s10_2","s10_3","s10_4"],"s9":["s9_1","s9_2","s9_3"],"s8":["s8_1","s8_2","s8_3"],
"s7":["s7_1","s7_2","s7_3"],"s6":["s6_1","s6_2","s6_3"],"s5":["s5_1","s5_2","s5_3"],
"s4":["s4_1","s4_2","s4_3"],"s3":["s3_1","s3_2","s3_3"],"s2":["s2_1","s2_2","s2_3"],"s1":["s1_1","s1_2","s1_3","s1_4","s1_5"]}
for k in ["s10","s9","s8","s7","s6","s5","s4","s3","s2","s1"]:
    cur=RAMP+0.1
    for kk in KEYS[k]: cur+=D[kk]+GAP
    sl=(cur-GAP)+POST+SWELL
    ab=start[k]+sl+4
    r=subprocess.run(["ffmpeg","-hide_banner","-nostats","-ss",f"{ab:.2f}","-t","12","-i",M,"-af","volumedetect","-f","null","/dev/null"],capture_output=True,text=True).stderr
    mv=[l.split("mean_volume:")[1].strip() for l in r.splitlines() if "mean_volume" in l]
    print(f"  {k:4} @{ab:6.1f}s  {mv[0] if mv else '?'}")
print("\nfinal dur:", subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",M],capture_output=True,text=True).stdout.strip())
