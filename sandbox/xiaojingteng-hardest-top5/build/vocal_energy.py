import sys, json
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
SCR=sys.argv[1]
def band(x, sr, lo, hi):
    sos = butter(4, [lo/(sr/2), hi/(sr/2)], btype='band', output='sos'); return sosfiltfilt(sos, x)
def rdb(x): return 20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
def analyze(clip, vseg):
    x, sr = sf.read(f"{SCR}/{clip}.wav")
    if x.ndim==1: x=np.stack([x,x],1)
    mid=(x[:,0]+x[:,1])/2; side=(x[:,0]-x[:,1])/2
    m_v=band(mid,sr,250,4000); s_v=band(side,sr,250,4000)
    m_lo=band(mid,sr,250,1500); m_hi=band(mid,sr,1500,5000)
    hop=int(0.5*sr); win=int(2.0*sr); n=len(mid); ts=[];loud=[];cen=[];bri=[]
    for i in range(0,n-win,hop):
        a=m_v[i:i+win]; b=s_v[i:i+win]
        ts.append(i/sr); loud.append(rdb(a)); cen.append(rdb(a)-rdb(b))
        bri.append(rdb(m_hi[i:i+win])-rdb(m_lo[i:i+win]))
    ts=np.array(ts);loud=np.array(loud);cen=np.array(cen);bri=np.array(bri)
    print(f"\n=== {clip} ===  (loud=vocalband dB, cen=centered, bri=high-note brightness)")
    rows=[]
    for s,e in vseg:
        msk=(ts>=s)&(ts<e)
        if msk.sum()==0: continue
        rows.append((float(np.median(loud[msk])+np.median(bri[msk])), s, e, e-s,
                     float(np.median(loud[msk])), float(np.median(cen[msk])), float(np.median(bri[msk]))))
    rows.sort(reverse=True)
    for score,s,e,d,lo,ce,br in rows[:6]:
        print(f"  vocal[{s:6.1f},{e:6.1f}] dur={d:4.1f}s  loud={lo:6.1f} cen={ce:5.1f} bri={br:6.1f}  SCORE={score:6.1f}")
va=json.load(open('probe/vocal_analysis.json'))
for clip in sys.argv[2:]:
    analyze(clip, va[clip]['vocal_segments'])
