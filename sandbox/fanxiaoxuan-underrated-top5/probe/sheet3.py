import subprocess
specs = {
 "win_tianmi":("live4k_tianmi",[18,32,46,60,72]),
 "win_yanlei":("live4k_yanlei",[40,54,68,82,92]),
 "scan_xiangni":("mv_xiangni",[10,45,85,130,175,220]),
 "scan_woyao":("mv_woyao",[10,45,85,130,175,220]),
 "win_pia":("ydtm_pia_live",[116,128,140,150,160]),
}
for tag,(v,ts) in specs.items():
    imgs=[]
    for t in ts:
        out=f"probe/{tag}_t{t}.png"
        subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f"raw/{v}.mp4","-frames:v","1",out,"-y"],check=True)
        imgs.append(out)
    ins=[]
    for im in imgs: ins+=["-i",im]
    fc="".join(f"[{i}:v]scale=300:-1[s{i}];" for i in range(len(imgs)))+"".join(f"[s{i}]" for i in range(len(imgs)))+f"hstack=inputs={len(imgs)}[o]"
    subprocess.run(["ffmpeg","-v","error",*ins,"-filter_complex",fc,"-map","[o]",f"probe/SHEET_{tag}.png","-y"],check=True)
    print("made",f"probe/SHEET_{tag}.png")
