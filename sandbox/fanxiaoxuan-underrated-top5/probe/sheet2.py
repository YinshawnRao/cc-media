import subprocess
specs = {
 "live4k_tianmi":[20,55,90,120,150],
 "live4k_yanlei":[30,90,150,210,260],
 "live4k_aishawuqi":[30,90,150,200,240],
 "mv_woyao":[20,70,120,170,220],
 "mv_rain":[20,70,120,170,210],
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
