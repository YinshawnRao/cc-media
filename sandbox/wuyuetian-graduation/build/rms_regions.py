import sys, subprocess, numpy as np, soundfile as sf
for k in sys.argv[1:]:
    subprocess.run(["ffmpeg","-v","error","-i",f"raw/{k}_full.mkv","-vn","-ac","1","-ar","22050",f"/tmp/{k}.wav","-y"],check=True)
    y,sr=sf.read(f"/tmp/{k}.wav")
    if y.ndim>1: y=y.mean(1)
    step=int(sr*1.0); win=int(sr*2.0)
    times=[]; vals=[]
    for i in range(0,len(y)-win,step):
        times.append(i/sr); vals.append(np.sqrt(np.mean(y[i:i+win]**2)))
    vals=np.array(vals); v=vals/vals.max()
    # smooth
    kern=np.ones(5)/5; vs=np.convolve(v,kern,'same')
    thr=0.62
    regions=[]; st=None
    for i,val in enumerate(vs):
        if val>=thr and st is None: st=times[i]
        elif val<thr and st is not None:
            if times[i]-st>=8: regions.append((round(st),round(times[i])))
            st=None
    if st is not None and times[-1]-st>=8: regions.append((round(st),round(times[-1])))
    print(f"{k} (dur {len(y)/sr:.0f}s) high-energy(≥0.62) ≥8s regions: {regions}")
