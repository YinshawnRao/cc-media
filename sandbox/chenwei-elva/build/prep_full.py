#!/usr/bin/env python3
"""全片素材预处理：8 首 showcase 切片+letterbox → hf_full/clips_seg/<key>_show.mp4，
各首 entry 静帧，woyao B站音轨，封面圆头像，narration durs.json。
从项目根运行：python3 build/prep_full.py
"""
import subprocess, json, wave, contextlib, shutil
from pathlib import Path

HF = Path("hf_full"); CS = HF/"clips_seg"; CA = HF/"cover_assets"
for d in (CS, CA): d.mkdir(parents=True, exist_ok=True)
def run(c): subprocess.run(c, check=True)
VFILL = "/Users/yinshawnrao/explorer/cc-media/tools/video/vfill.sh"

# key, src, crop(native), win_start, showd, still_t
SONGS = [
 ("meiyouren","raw/meiyouren_src.mp4","648:300:0:0",200,30,224),
 ("turan",    "raw/turan_src.webm",   "648:300:0:0",144,32,160),
 ("yuji",     "raw/yuji_src.webm",    "1600:798:0:148",207,30,215),
 ("mingtian", "raw/mingtian_src.webm","712:354:0:46",204,30,206),
 ("woaini",   "raw/woaini_src.webm",  "712:360:0:0",149,30,152),
 ("woxihuan", "raw/woxihuan_src.webm","712:350:0:0",66,30,82),
 ("aida",     "raw/aida_src.webm",    "712:320:0:58",136,30,150),
 ("woyao",    "raw/woyao_bili.mp4",   "1440:800:0:140",194,30,206),
]

# woyao B站 实际扩展名探测
import glob
wb = glob.glob("raw/woyao_bili.*")[0]

for key, src, crop, ws, showd, st in SONGS:
    if key == "woyao": src = wb
    cutdur = showd + 4
    tmp = f"clips/{key}_cut.mp4"
    Path("clips").mkdir(exist_ok=True)
    # 输出端 seek 精确切（webm/av1/mkv 重编码 h264+aac，含音频供 vfill）
    run(["ffmpeg","-v","error","-i",src,"-ss",str(ws),"-t",str(cutdur),
         "-c:v","libx264","-preset","veryfast","-g","30","-keyint_min","30",
         "-c:a","aac","-b:a","192k",tmp,"-y"])
    # letterbox
    run(["bash",VFILL,tmp,str(CS/f"{key}_show.mp4"),crop,"-0.26","1.05"])
    # entry 静帧（裁同 crop 去烧词；relative 到本片起点 st 为源秒）
    run(["ffmpeg","-v","error","-i",src,"-ss",str(st),"-frames:v","1",
         "-vf",f"crop={crop}",str(CA/f"{key}_entry.jpg"),"-y"])
    print(f"  {key}: show + entry done")

# woyao B站 全曲 wav（覆盖 dl_rest 里 Jazz Li 的）
run(["ffmpeg","-v","error","-i",wb,"-vn","-ac","2","-ar","48000","-c:a","pcm_s16le","raw/woyao_full.wav","-y"])
print("  woyao_full.wav <- B站")

# 封面圆头像
shutil.copy("cover_assets/aida_face.png", str(CA/"aida_face.png"))
shutil.copy("cover_assets/still_132.jpg", str(CA/"meiyouren_bg.jpg"))  # 封面暗背景备用

# narration durs.json
durs = {}
for w in sorted(Path("audio_full").glob("*.wav")):
    with contextlib.closing(wave.open(str(w),'r')) as wf:
        durs[w.stem] = round(wf.getnframes()/wf.getframerate(),3)
Path("audio_full/durs.json").write_text(json.dumps(durs, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"durs.json: {len(durs)} clips")
print("PREP DONE")
