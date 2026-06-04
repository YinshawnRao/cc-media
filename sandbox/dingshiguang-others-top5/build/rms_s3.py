import librosa, numpy as np
y,sr = librosa.load("raw/s3_ailaiguo.wav", sr=22050, mono=True)
hop=2205
rms = librosa.feature.rms(y=y, frame_length=4410, hop_length=hop)[0]
db = librosa.amplitude_to_db(rms+1e-8)
sm = np.convolve(db, np.ones(30)/30, mode='same')
print(f"=== 爱来过 studio (OST MV audio) dur={len(y)/sr:.0f}s ===")
prof=[f"{s:3d}s:{sm[int(s*sr/hop)]:5.1f}" for s in range(0,int(len(y)/sr),8) if int(s*sr/hop)<len(sm)]
print("  ".join(prof))
win=int(12*sr/hop); best=[]
for i in range(0,len(sm)-win,int(2*sr/hop)): best.append((sm[i:i+win].mean(), i*hop/sr))
best.sort(reverse=True); picked=[]
for m,ts in best:
    if all(abs(ts-p)>15 for p in picked):
        picked.append(ts)
        if len(picked)>=4: break
print("chorus-cand:", ", ".join(f"{p:.0f}s" for p in sorted(picked)))
