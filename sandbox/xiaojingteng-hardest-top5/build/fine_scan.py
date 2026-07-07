import sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
SCR=sys.argv[1]
def band(x,sr,lo,hi):
    sos=butter(4,[lo/(sr/2),hi/(sr/2)],btype='band',output='sos');return sosfiltfilt(sos,x)
def rdb(x):return 20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
def scan(clip,t0,t1):
    x,sr=sf.read(f"{SCR}/{clip}.wav")
    if x.ndim==1:x=np.stack([x,x],1)
    mid=(x[:,0]+x[:,1])/2;side=(x[:,0]-x[:,1])/2
    mv=band(mid,sr,250,4000);sv=band(side,sr,250,4000)
    mlo=band(mid,sr,250,1500);mhi=band(mid,sr,1500,5000)
    print(f"\n=== {clip} {t0}-{t1}s  (sec: loud cen bri  bar) ===")
    for t in range(int(t0),int(t1)):
        i=int(t*sr);j=int((t+1)*sr)
        lo=rdb(mv[i:j]);ce=rdb(mv[i:j])-rdb(sv[i:j]);br=rdb(mhi[i:j])-rdb(mlo[i:j])
        bar='#'*max(0,int((lo+30)))
        print(f"  {t:5d}s  {lo:6.1f} {ce:5.1f} {br:6.1f}  {bar}")
scan('vert_wangzidexinyi',214,253)
scan('vert_zenmeshuo',146,186)
