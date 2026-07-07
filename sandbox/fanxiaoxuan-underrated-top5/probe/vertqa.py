import subprocess
clips=["p1_kanbujian","p2_dushini","p3_trust","p4_yinwei","p5_pangzi"]
ts=[6,22,33,44]
for key in clips:
    imgs=[]
    for t in ts:
        out=f"probe/vqa_{key}_t{t}.png"
        subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f"clips/vert_{key}.mp4","-frames:v","1",out,"-y"],check=True)
        imgs.append(out)
    ins=[]
    for im in imgs: ins+=["-i",im]
    fc="".join(f"[{i}:v]scale=240:-1[s{i}];" for i in range(len(imgs)))+"".join(f"[s{i}]" for i in range(len(imgs)))+f"hstack=inputs={len(imgs)}[o]"
    subprocess.run(["ffmpeg","-v","error",*ins,"-filter_complex",fc,"-map","[o]",f"probe/VQA_{key}.png","-y"],check=True)
    print("VQA",key)
