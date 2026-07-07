import subprocess
scans={
 "woyao_late":("mv_woyao",[160,172,184,196,205,230]),
 "woyao_early":("mv_woyao",[30,55,70,90,100]),
 "xiangni_win":("mv_xiangni",[42,56,70,84,92]),
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
    print("scan",tag)
