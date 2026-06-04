import librosa, numpy as np, sys
songs = {
 "s1_xinsuan_redbull":"心酸(redbull live)",
 "s2_catherine":"Catherine(MV)",
 "s4_lvgu":"肋骨(LUNAR live)",
 "s5_fengci":"讽刺的情书(MV)",
}
for key,label in songs.items():
    y,sr = librosa.load(f"raw/{key}.wav", sr=22050, mono=True)
    hop=2205  # 0.1s
    rms = librosa.feature.rms(y=y, frame_length=4410, hop_length=hop)[0]
    db = librosa.amplitude_to_db(rms+1e-8)
    # smooth over ~3s
    w=30
    sm = np.convolve(db, np.ones(w)/w, mode='same')
    t = np.arange(len(sm))*hop/sr
    # print energy profile every 10s + top sustained windows
    print(f"\n=== {label}  dur={len(y)/sr:.0f}s ===")
    prof=[]
    for s in range(0,int(len(y)/sr),10):
        i=int(s*sr/hop); 
        if i<len(sm): prof.append(f"{s:3d}s:{sm[i]:5.1f}")
    print("  ".join(prof))
    # find 12s windows with highest mean smoothed energy (chorus candidates)
    win=int(12*sr/hop)
    best=[]
    for i in range(0,len(sm)-win,int(2*sr/hop)):
        best.append((sm[i:i+win].mean(), i*hop/sr))
    best.sort(reverse=True)
    picked=[]
    for m,ts in best:
        if all(abs(ts-p)>15 for p in picked):
            picked.append(ts); 
            if len(picked)>=4: break
    print("  chorus-cand (12s win, top4):", ", ".join(f"{p:.0f}s({[b[0] for b in best if abs(b[1]-p)<0.6][0]:.1f}dB)" for p in sorted(picked)))
