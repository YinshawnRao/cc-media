import numpy as np, soundfile as sf, sys
from pathlib import Path
def scan(key, win=5.0, lo=0.30):
    p = Path("raw")/f"{key}.wav"
    y, sr = sf.read(str(p))
    if y.ndim>1: y = y.mean(axis=1)
    dur = len(y)/sr
    print(f"== {key}  dur={dur:.1f}s ==")
    n = int(win*sr); peaks=[]
    for s in range(int(dur*lo), int(dur-win), int(win)):
        seg = y[s*sr:s*sr+n]
        if len(seg)<n: break
        rms = np.sqrt(np.mean(seg**2)+1e-12)
        db = 20*np.log10(rms+1e-12)
        peaks.append((s,db))
    mx = max(d for _,d in peaks)
    for s,db in peaks:
        bar = "#"*int((db+40))
        flag = " <== PEAK" if db>mx-1.2 else ""
        print(f"  {s//60}:{s%60:02d} ({s:3d}s)  {db:6.1f}dB {bar}{flag}")
for k in ["s1","s2","s3","s4","s5_bi","s5_yt"]:
    scan(k); print()
