import sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
SCR=sys.argv[1]
def band(x,sr,lo,hi):
    sos=butter(4,[lo/(sr/2),hi/(sr/2)],btype='band',output='sos');return sosfiltfilt(sos,x)
def rdb(x):return 20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
x,sr=sf.read(f"{SCR}/vert_zenmeshuo.wav")
mid=(x[:,0]+x[:,1])/2;side=(x[:,0]-x[:,1])/2
mv=band(mid,sr,250,4000);sv=band(side,sr,250,4000)
mlo=band(mid,sr,250,1500);mhi=band(mid,sr,1500,5000)
print("zenmeshuo 218-245s (loud cen bri):")
for t in range(218,245):
    i=int(t*sr);j=int((t+1)*sr)
    lo=rdb(mv[i:j]);ce=rdb(mv[i:j])-rdb(sv[i:j]);br=rdb(mhi[i:j])-rdb(mlo[i:j])
    print(f"  {t}s {lo:6.1f} {ce:5.1f} {br:6.1f}  {'#'*max(0,int(lo+30))}")
