import subprocess
# cover face candidates (source frames, full res)
cands=[
 ("woyao196","mv_woyao",196.5),
 ("woyao206","mv_woyao",206),
 ("tianmi_a","live4k_tianmi",46),
 ("tianmi_b","live4k_tianmi",100),
 ("aisha230","live4k_aishawuqi",230),
 ("xiangni92","mv_xiangni",92),
 ("xiangni136","mv_xiangni",136),
]
for tag,v,t in cands:
    subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f"raw/{v}.mp4","-frames:v","1",f"probe/cov_{tag}.png","-y"],check=True)
# montage
ins=[]; tags=[c[0] for c in cands]
for tag in tags: ins+=["-i",f"probe/cov_{tag}.png"]
fc="".join(f"[{i}:v]scale=260:-1,pad=iw:ih+24:0:24:black[s{i}];" for i in range(len(tags)))+"".join(f"[s{i}]" for i in range(len(tags)))+f"hstack=inputs={len(tags)}[o]"
subprocess.run(["ffmpeg","-v","error",*ins,"-filter_complex",fc,"-map","[o]","probe/COVER_CANDS.png","-y"],check=True)
print("made COVER_CANDS",tags)
