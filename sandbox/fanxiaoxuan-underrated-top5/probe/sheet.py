import subprocess, sys, os
specs = {
 "kanbujian_leejupiter":[20,70,120,180,240],
 "mv_xiangni":[15,60,110,170,220],
 "mv_shuzilianai":[15,60,110,170,220],
 "shikong_S":[15,60,110,160,200],
 "ydtm_pia_live":[15,50,90,120,150],
}
for v,ts in specs.items():
    imgs=[]
    for t in ts:
        out=f"probe/{v}_t{t}.png"
        subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f"raw/{v}.mp4","-frames:v","1",out,"-y"],check=True)
        imgs.append(out)
    ins=[]
    for im in imgs: ins+=["-i",im]
    fc="".join(f"[{i}:v]scale=320:-1[s{i}];" for i in range(len(imgs)))+"".join(f"[s{i}]" for i in range(len(imgs)))+f"hstack=inputs={len(imgs)}[o]"
    subprocess.run(["ffmpeg","-v","error",*ins,"-filter_complex",fc,"-map","[o]",f"probe/SHEET_{v}.png","-y"],check=True)
    print("made",f"probe/SHEET_{v}.png")
