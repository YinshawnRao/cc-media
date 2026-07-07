import subprocess
scans={
 "xiangni_late":("mv_xiangni",[100,118,136,150,168,180]),
 "woyao_show":("mv_woyao",[176,186,196,206,216]),
}
for tag,(v,ts) in scans.items():
    imgs=[]
    for t in ts:
        out=f"probe/{tag}_t{t}.png"
        subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f"raw/{v}.mp4","-frames:v","1",out,"-y"],check=True)
        imgs.append(out)
    ins=[]
    for im in imgs: ins+=["-i",im]
    fc="".join(f"[{i}:v]scale=300:-1[s{i}];" for i in range(len(imgs)))+"".join(f"[s{i}]" for i in range(len(imgs)))+f"hstack=inputs={len(imgs)}[o]"
    subprocess.run(["ffmpeg","-v","error",*ins,"-filter_complex",fc,"-map","[o]",f"probe/SHEET_{tag}.png","-y"],check=True)
    print(tag)
