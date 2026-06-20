import sys, subprocess, numpy as np, soundfile as sf, os
for k in sys.argv[1:]:
    src=f"raw/{k}_full.mkv"; wav=f"/tmp/{k}.wav"
    subprocess.run(["ffmpeg","-v","error","-i",src,"-vn","-ac","1","-ar","22050",wav,"-y"],check=True)
    y,sr=sf.read(wav);
    if y.ndim>1: y=y.mean(1)
    win=int(sr*2);
    rms=[(i/sr, float(np.sqrt(np.mean(y[i:i+win]**2)))) for i in range(0,len(y)-win,int(sr*2))]
    mx=max(r for _,r in rms)
    print(f"\n=== {k} (dur {len(y)/sr:.0f}s) peak-normalized RMS per 2s ===")
    line=""
    for t,r in rms:
        bar="#"*int(r/mx*30)
        line=f"{t:5.0f}s |{bar:<30}| {r/mx:.2f}"
        print(line)
