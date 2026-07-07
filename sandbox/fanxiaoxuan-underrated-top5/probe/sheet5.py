import subprocess
# crop-band strips
strips=[
 ("tianmi_BOT","live4k_tianmi",40,"crop=1920:130:0:950"),
 ("aisha_TOP","live4k_aishawuqi",70,"crop=1832:90:0:0"),
 ("aisha_BOT","live4k_aishawuqi",70,"crop=1832:140:0:940"),
 ("woyao_full","mv_woyao",130,None),
 ("xiangni_full","mv_xiangni",60,None),
]
for tag,v,t,crop in strips:
    args=["ffmpeg","-v","error","-ss",str(t),"-i",f"raw/{v}.mp4"]
    if crop: args+=["-vf",crop]
    args+=["-frames:v","1",f"probe/STRIP_{tag}.png","-y"]
    subprocess.run(args,check=True)
    print("strip",tag)
# window scans (find dense close-up windows)
scans={
 "aisha_win":("live4k_aishawuqi",[200,215,230,245,255]),
 "woyao_win":("mv_woyao",[108,120,132,144,156]),
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
