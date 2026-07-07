import subprocess
specs={
 "pia_full":("ydtm_pia_live",[8,30,55,75,100,145]),
 "aisha_check":("live4k_aishawuqi",[25,70,120,170,230]),
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
